import QtQuick
import QtQuick.Controls

AbstractButton {
    id: control
    property bool primary: false
    property bool selected: false
    property string symbol: ""
    implicitHeight: 42
    implicitWidth: label.implicitWidth + 32
    hoverEnabled: true
    Accessible.name: text
    contentItem: ZText {
        id: label
        text: (control.symbol ? control.symbol + "   " : "") + control.text
        color: control.primary ? "#062a2b" : control.selected ? "#6cf1d2" : "#c3d2e3"
        font.pixelSize: 13
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.NoWrap
    }
    background: Rectangle {
        radius: 12
        color: control.primary ? (control.hovered ? "#8bfadd" : "#58dfc0") : control.selected ? "#1b3e48" : control.hovered ? "#203346" : "#132331"
        border.color: control.activeFocus ? "#b6ffee" : control.selected ? "#366b70" : "#2a3d50"
        border.width: control.activeFocus ? 2 : 1
        Behavior on color {
            ColorAnimation {
                duration: 140
            }
        }
    }
    scale: down ? 0.97 : 1
    Behavior on scale {
        NumberAnimation {
            duration: 100
        }
    }
    opacity: enabled ? 1 : 0.45
}
