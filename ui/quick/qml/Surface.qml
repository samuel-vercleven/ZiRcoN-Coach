import QtQuick

Rectangle {
    id: surface
    property color tint: ZTheme.color("#182938")
    radius: 22
    border.color: ZTheme.color("#304458")
    border.width: 1
    gradient: Gradient {
        GradientStop {
            position: 0
            color: surface.tint
        }
        GradientStop {
            position: 1
            color: ZTheme.color("#0f1b28")
        }
    }
    // Native shapes retain depth in both GPU and software renderers.
    Rectangle {
        z: -1
        x: 3
        y: 8
        width: parent.width
        height: parent.height
        radius: parent.radius
        color: ZTheme.color("#50000000")
    }
    Rectangle {
        x: 24
        y: 1
        width: Math.max(0, parent.width - 48)
        height: 1
        color: ZTheme.color("#376986")
        opacity: 0.45
    }
}
