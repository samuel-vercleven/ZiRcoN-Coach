import QtQuick
import QtQuick.Controls

Item {
    id: root
    property var values: []
    property var labels: []
    property string unit: ""
    property real fixedMaximum: 0
    property int selected: -1
    readonly property real maximum: fixedMaximum || Math.max(1, ...values.filter(v => v !== null))
    implicitHeight: 218
    function px(index) {
        return 44 + (width - 58) * index / Math.max(1, values.length - 1);
    }
    function py(value) {
        return 14 + (height - 62) * (1 - value / maximum);
    }
    onValuesChanged: plot.requestPaint()
    onWidthChanged: plot.requestPaint()
    onHeightChanged: plot.requestPaint()
    Connections {
        target: ZTheme
        function onBelvethChanged() {
            plot.requestPaint();
        }
    }
    Canvas {
        id: plot
        anchors.fill: parent
        onPaint: {
            let ctx = getContext("2d");
            ctx.reset();
            ctx.font = "11px Segoe UI";
            for (let i = 0; i < 3; ++i) {
                const value = root.maximum * (1 - i / 2), y = root.py(value);
                ctx.strokeStyle = ZTheme.color("#253a4d");
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(44, y);
                ctx.lineTo(width - 14, y);
                ctx.stroke();
                ctx.fillStyle = ZTheme.color("#92a9c1");
                ctx.fillText(value.toFixed(1), 2, y + 4);
            }
            ctx.strokeStyle = ZTheme.color("#62e6c5");
            ctx.lineWidth = 2;
            for (let i = 0; i < root.values.length; ++i) {
                const value = root.values[i];
                if (value === null)
                    continue;
                const x = root.px(i), y = root.py(value);
                if (i > 0 && root.values[i - 1] !== null) {
                    ctx.beginPath();
                    ctx.moveTo(root.px(i - 1), root.py(root.values[i - 1]));
                    ctx.lineTo(x, y);
                    ctx.stroke();
                }
                ctx.fillStyle = ZTheme.color("#62e6c5");
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.fillStyle = ZTheme.color("#92a9c1");
            ctx.fillText("Plus anciennes", 44, height - 10);
            ctx.fillText("Plus récentes", width - 90, height - 10);
        }
    }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onPositionChanged: mouse => root.selected = root.values.length ? Math.max(0, Math.min(root.values.length - 1, Math.round((mouse.x - 44) / (root.width - 58) * Math.max(1, root.values.length - 1)))) : -1
        onExited: root.selected = -1
        ToolTip.visible: root.selected >= 0
        ToolTip.text: root.selected < 0 ? "" : root.labels[root.selected] + " · " + (root.values[root.selected] === null ? "Donnée manquante" : Number(root.values[root.selected]).toFixed(1) + " " + root.unit)
    }
    ZText {
        visible: root.values.length === 0
        anchors.centerIn: parent
        text: "Pas encore de parties dans cette période."
        font.pixelSize: 12
        color: ZTheme.color("#a6bfd3")
    }
}
