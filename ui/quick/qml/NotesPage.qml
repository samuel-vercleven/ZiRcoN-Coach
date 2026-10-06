import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Surface {
    id: root
    property var game: ({})
    property string matchIdentity: game.id || ""
    property bool starred: false
    property bool dirty: false
    property bool loading: false
    property string loadedIdentity: ""
    property var drafts: ({})
    property string draftScope: ""
    Component.onCompleted: draftScope = coach ? (coach.state.noteScope || "") : ""
    property int draftCount: 0
    readonly property bool hasDrafts: draftCount > 0
    property string lastDraft: ""
    onMatchIdentityChanged: {
        loading = true;
        loadedIdentity = matchIdentity;
        const draft = drafts[matchIdentity];
        editor.text = draft ? draft.note : ((game.journal || {}).note || "");
        starred = draft ? draft.starred : ((game.journal || {}).starred || false);
        dirty = !!draft;
        loading = false;
    }
    function remember() {
        if (loading || !loadedIdentity)
            return;
        const journal = game.journal || ({});
        if (editor.text === (journal.note || "") && starred === (journal.starred || false)) {
            delete drafts[loadedIdentity];
            draftCount = Object.keys(drafts).length;
            dirty = false;
            return;
        }
        drafts[loadedIdentity] = {
            note: editor.text,
            starred: starred
        };
        draftCount = Object.keys(drafts).length;
        lastDraft = loadedIdentity;
        dirty = true;
    }
    onStarredChanged: remember()
    Connections {
        target: coach
        function onRefreshed() {
            const scope = coach.state.noteScope || "";
            if (scope !== root.draftScope) {
                root.drafts = ({});
                root.dirty = false;
                root.loadedIdentity = "";
                root.draftCount = 0;
                root.lastDraft = "";
                root.draftScope = scope;
            }
        }
    }
    Layout.fillWidth: true
    implicitHeight: body.implicitHeight + 48
    ColumnLayout {
        id: body
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: 24
        }
        spacing: 16
        ZText {
            text: "Ce que tu veux garder de cette partie"
            font.pixelSize: 24
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        ZText {
            text: "Une idée à tester, un moment à revoir… Tes notes restent enregistrées localement."
            color: ZTheme.color("#a6bfd3")
            Layout.fillWidth: true
        }
        ZButton {
            text: root.starred ? "★ Partie dans mes favoris" : "☆ Ajouter aux favoris"
            selected: root.starred
            onClicked: root.starred = !root.starred
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 238
            radius: 12
            color: ZTheme.color("#152638")
            border.color: editor.activeFocus ? ZTheme.color("#65d8c5") : ZTheme.color("#30485d")
            ScrollView {
                anchors.fill: parent
                anchors.margins: 12
                clip: true
                TextArea {
                    id: editor
                    objectName: "matchNoteEditor"
                    color: ZTheme.color("#edf3fa")
                    font.family: "Segoe UI"
                    font.pixelSize: 15
                    placeholderText: "Mon prochain réflexe…"
                    placeholderTextColor: ZTheme.color("#8aa3bd")
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    onTextChanged: {
                        if (text.length > 1000)
                            text = text.slice(0, 1000);
                        root.remember();
                    }
                    background: null
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            ZText {
                text: (root.dirty ? "Non enregistré · " : "") + editor.text.length + " / 1000 caractères"
                color: ZTheme.color("#95acc3")
                font.pixelSize: 12
                Layout.fillWidth: true
            }
            ZButton {
                objectName: "saveNoteButton"
                text: "Enregistrer ma note"
                primary: true
                onClicked: {
                    if (coach.saveJournal(root.matchIdentity, root.starred, editor.text)) {
                        delete root.drafts[root.matchIdentity];
                        root.draftCount = Object.keys(root.drafts).length;
                        root.dirty = false;
                    }
                }
            }
        }
    }
}
