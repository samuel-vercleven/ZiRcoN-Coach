import QtQuick
import QtQuick.Controls

ComboBox {
    id: control
    implicitHeight: 42
    implicitWidth: 164
    font.family: "Segoe UI"
    font.pixelSize: 13
    contentItem: ZText {
        text: control.displayText
        leftPadding: 12
        rightPadding: 28
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        wrapMode: Text.NoWrap
    }
    background: Rectangle {
        radius: 10
        color: ZTheme.color("#152638")
        border.color: control.activeFocus ? ZTheme.color("#65d8c5") : ZTheme.color("#30485d")
    }
    delegate: ItemDelegate {
        width: control.width
        contentItem: ZText {
            text: modelData
            color: ZTheme.color("#edf3fa")
            font.pixelSize: 13
            wrapMode: Text.NoWrap
            elide: Text.ElideRight
        }
        background: Rectangle {
            color: parent.highlighted ? ZTheme.color("#1e3549") : ZTheme.color("#132331")
        }
        highlighted: control.highlightedIndex === index
    }
    popup: Popup {
        y: control.height + 4
        width: control.width
        padding: 4
        implicitHeight: Math.min(300, contentItem.implicitHeight + 8)
        background: Rectangle {
            radius: 10
            color: ZTheme.color("#132331")
            border.color: ZTheme.color("#30485d")
        }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollBar.vertical: ScrollBar {}
        }
    }
}
