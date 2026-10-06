import QtQuick

Item {
    id: root
    property real value: 0
    width: 94
    height: 94
    Canvas {
        id: ring
        anchors.fill: parent
        onPaint: {
            let ctx = getContext("2d");
            ctx.reset();
            ctx.lineWidth = 7;
            ctx.lineCap = "round";
            ctx.strokeStyle = ZTheme.color("#244452");
            ctx.beginPath();
            ctx.arc(47, 47, 38, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.strokeStyle = root.value >= 70 ? ZTheme.color("#61e4c7") : root.value >= 45 ? ZTheme.color("#efc578") : ZTheme.color("#f18b9a");
            ctx.beginPath();
            ctx.arc(47, 47, 38, -Math.PI / 2, -Math.PI / 2 + Math.max(0, Math.min(100, root.value)) / 100 * Math.PI * 2);
            ctx.stroke();
        }
    }
    onValueChanged: ring.requestPaint()
    Connections {
        target: ZTheme
        function onBelvethChanged() {
            ring.requestPaint();
        }
    }
    ZText {
        anchors.centerIn: parent
        text: Math.round(root.value)
        font.pixelSize: 26
        font.bold: true
    }
    Accessible.name: "Repère de pertinence indicatif : " + Math.round(value) + ". Ce n’est pas une probabilité."
}
