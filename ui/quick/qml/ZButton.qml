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
        color: control.primary ? ZTheme.color("#062a2b") : control.selected ? ZTheme.color("#6cf1d2") : ZTheme.color("#c3d2e3")
        font.pixelSize: 13
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.NoWrap
    }
    background: Rectangle {
        radius: 12
        color: control.primary ? (control.hovered ? ZTheme.color("#8bfadd") : ZTheme.color("#58dfc0")) : control.selected ? ZTheme.color("#1b3e48") : control.hovered ? ZTheme.color("#203346") : ZTheme.color("#132331")
        border.color: control.activeFocus ? ZTheme.color("#b6ffee") : control.selected ? ZTheme.color("#366b70") : ZTheme.color("#2a3d50")
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
