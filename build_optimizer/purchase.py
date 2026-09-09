"""Recipe-only feasibility. Never claims complete in-client purchase legality."""
from collections import Counter
from dataclasses import asdict, dataclass

from analysis.itemization_analyzer import _consume_component_tree, _slot_count
from build_optimizer.catalog import CatalogView, natural

MAX_SEARCH_STATES = 5000  # Resource bound, not a gameplay threshold; truncation is explicit.
MAX_INVENTORY_SLOTS = 6  # Existing v22 durable-inventory contract.


@dataclass(frozen=True)
class PurchaseStep:
    item_id: int
    cost: int
    consumed: tuple[int, ...]
    inventory_after: tuple[int, ...]


@dataclass(frozen=True)
class RecipePlan:
    target_item: int
    status: str
    steps: tuple[PurchaseStep, ...]
    total_spend: int
    remaining_cost_before: int | None
    remaining_cost_after: int | None
    target_completed: bool
    warnings: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class RecipePlanner:
    def __init__(self, catalog: CatalogView):
        self.catalog = catalog
        self.reconstruction = catalog.reconstruction_catalog()

    def _graph_valid(self, item_id, visiting=()):
        if not natural(item_id, True):
            return False
        item = self.catalog.items.get(item_id)
        if item is None or item_id in visiting or item.structural_blockers:
            return False
        if not all(self._graph_valid(c, (*visiting, item_id)) for c in item.components):
            return False
        return item.total_cost == item.purchase_cost + sum(self.catalog.items[c].total_cost for c in item.components)

    def quote(self, inventory, item_id):
        """Marginal price after actual v22 component consumption; no double credit."""
        if not all(natural(i, True) and i in self.catalog.items for i in inventory):
            return None
        if _slot_count(Counter(inventory), self.reconstruction) > MAX_INVENTORY_SLOTS:
            return None
        if not self._graph_valid(item_id):
            return None
        item = self.catalog.items[item_id]
        remaining = Counter(inventory)
        consumed = []
        for component in item.components:
            _consume_component_tree(remaining, component, self.reconstruction, consumed)
        credit = sum(self.catalog.items[c].total_cost for c in consumed)
        cost = item.total_cost - credit
        remaining[item_id] += 1
        if cost < 0 or _slot_count(remaining, self.reconstruction) > MAX_INVENTORY_SLOTS:
            return None
        return PurchaseStep(item_id, cost, tuple(sorted(consumed)),
                            tuple(sorted(i for i, n in remaining.items() for _ in range(n))))

    def _needed(self, target, inventory):
        available = Counter(inventory)
        wanted = []

        def visit(item_id):
            if available[item_id]:
                available[item_id] -= 1
                return
            wanted.append(item_id)
            for component in self.catalog.items[item_id].components:
                visit(component)

        visit(target)
        return sorted(set(wanted))

    def plan(self, target, inventory, gold):
        def blocked(reason):
            return RecipePlan(target, 'BLOCKED', (), 0, None, None, False, (reason,))

        if not natural(gold):
            return blocked('BUDGET_UNRESOLVED')
        if not all(natural(i, True) and i in self.catalog.items for i in inventory):
            return blocked('INVENTORY_UNRESOLVED')
        if _slot_count(Counter(inventory), self.reconstruction) > MAX_INVENTORY_SLOTS:
            return blocked('INVENTORY_OVER_CAPACITY')
        if not self._graph_valid(target):
            return blocked('RECIPE_OR_APPLICABILITY_UNRESOLVED')
        if target in inventory:
            return blocked('TARGET_ALREADY_OWNED')
        # Cost before is meaningful even when no free slot exists: credit is
        # calculated using frozen consumption; capacity affects each actual step.
        def remaining_cost(held):
            if target in held:
                return 0
            counter, consumed = Counter(held), []
            for component in self.catalog.items[target].components:
                _consume_component_tree(counter, component, self.reconstruction, consumed)
            return self.catalog.items[target].total_cost - sum(self.catalog.items[c].total_cost for c in consumed)

        initial_cost = remaining_cost(inventory)
        queue = [(tuple(sorted(inventory)), gold, ())]
        seen = set()
        best = (False, 0, 0)
        best_steps, best_remaining = (), initial_cost
        truncated = False
        while queue:
            held, budget, steps = queue.pop()
            key = held, budget
            if key in seen:
                continue
            seen.add(key)
            if len(seen) > MAX_SEARCH_STATES:
                truncated = True
                break
            remaining = remaining_cost(held)
            quality = (target in held, initial_cost - remaining, -(gold - budget))
            if quality > best:
                best, best_steps, best_remaining = quality, steps, remaining
            if target in held:
                continue
            for item_id in reversed(self._needed(target, held)):
                step = self.quote(held, item_id)
                if step is not None and step.cost <= budget:
                    queue.append((step.inventory_after, budget - step.cost, (*steps, step)))
        warnings = ['SHOP_ACCESS_UNMODELED', 'PURCHASE_RESTRICTIONS_UNMODELED', 'RECIPE_ONLY_NOT_GAMEPLAY_OPTIMAL']
        if truncated:
            warnings.append('SEARCH_LIMIT_REACHED')
        return RecipePlan(target, 'PARTIAL', best_steps, sum(s.cost for s in best_steps), initial_cost,
                          best_remaining, bool(best[0]), tuple(warnings))

    def candidates(self, inventory, gold):
        return tuple(self.plan(i, inventory, gold) for i, item in sorted(self.catalog.items.items())
                     if not item.structural_blockers and i not in inventory and self._graph_valid(i))
