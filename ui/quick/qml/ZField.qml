import QtQuick
import QtQuick.Controls

TextField {
    readonly property bool passwordProtected: echoMode === TextInput.Password
    implicitHeight: 46
    color: ZTheme.color("#edf3fa")
    placeholderTextColor: ZTheme.color("#8aa3bd")
    font.family: "Segoe UI"
    font.pixelSize: 14
    leftPadding: 14
    rightPadding: 14
    selectByMouse: true
    background: Rectangle {
        radius: 10
        color: ZTheme.color("#152638")
        border.color: parent.activeFocus ? ZTheme.color("#65d8c5") : ZTheme.color("#30485d")
        border.width: parent.activeFocus ? 2 : 1
    }
}
