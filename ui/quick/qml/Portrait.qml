import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    property string kind: "champion"
    property string identity: ""
    property string version: ""
    property string description: identity
    width: 38
    height: width
    radius: 8
    color: ZTheme.color("#203448")
    clip: true
    visible: identity !== "" && identity !== "0"
    Image {
        anchors.fill: parent
        anchors.margins: 1
        source: {
            if (!coach)
                return "";
            let revision = coach.assetRevision;
            return coach.assetUrl(root.kind, root.identity, root.version);
        }
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: true
    }
    border.color: ZTheme.color("#496078")
    border.width: 1
    Accessible.name: description
    HoverHandler {
        id: hover
    }
    ToolTip.visible: hover.hovered
    ToolTip.delay: 400
    ToolTip.text: kind === "item" && description === identity ? "Objet de la partie" : description
}
