import QtQuick
import QtQuick.Controls

Item {
    id: root
    property var points: []
    property int selected: -1
    readonly property real maximum: Math.max(1000, ...points.map(p => p.delta === null ? 0 : Math.abs(p.delta || 0)))
    readonly property real endTime: Math.max(1, points.length ? points[points.length - 1].timestamp : 1)
    implicitHeight: 218
    function sx(p) {
        return 52 + (width - 70) * p.timestamp / endTime;
    }
    function sy(p) {
        return 22 + (height - 62) / 2 * (1 - p.delta / maximum);
    }
    function time(ms) {
        let sec = Math.floor(ms / 1000);
        return Math.floor(sec / 60) + ":" + ("0" + sec % 60).slice(-2);
    }
    onPointsChanged: plot.requestPaint()
    onWidthChanged: plot.requestPaint()
    onHeightChanged: plot.requestPaint()
    Connections {
        target: ZTheme
        function onBelvethChanged() { plot.requestPaint() }
    }
    Canvas {
        id: plot
        anchors.fill: parent
        onPaint: {
            let ctx = getContext("2d");
            ctx.reset();
            const area = height - 62, middle = 22 + area / 2;
            ctx.font = "11px Segoe UI";
            ctx.fillStyle = ZTheme.color("#92a9c1");
            for (let i = 0; i < 5; ++i) {
                const y = 22 + i * area / 4, value = root.maximum * (1 - i / 2);
                ctx.strokeStyle = i === 2 ? ZTheme.color("#5b748c") : ZTheme.color("#253a4d");
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(52, y);
                ctx.lineTo(width - 18, y);
                ctx.stroke();
                ctx.fillText((value > 0 ? "+" : "") + (value / 1000).toFixed(1) + "k", 4, y + 4);
            }
            for (let i = 0; i < 5; ++i) {
                const stamp = root.endTime * i / 4;
                ctx.fillText(root.time(stamp), 44 + (width - 70) * i / 4, height - 14);
            }
            ctx.lineWidth = 2.5;
            for (let i = 1; i < root.points.length; ++i) {
                const a = root.points[i - 1], b = root.points[i];
                if (a.delta === null || b.delta === null || a.delta === undefined || b.delta === undefined)
                    continue;
                const x1 = root.sx(a), y1 = root.sy(a), x2 = root.sx(b), y2 = root.sy(b);
                // Split sign-changing segments at zero; never interpolate across missing observations.
                const cut = a.delta * b.delta < 0;
                const splitX = cut ? x1 + (x2 - x1) * Math.abs(a.delta) / (Math.abs(a.delta) + Math.abs(b.delta)) : x2;
                ctx.strokeStyle = a.delta >= 0 ? ZTheme.color("#62e6c5") : ZTheme.color("#f48a9b");
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(splitX, cut ? middle : y2);
                ctx.stroke();
                if (cut) {
                    ctx.strokeStyle = b.delta >= 0 ? ZTheme.color("#62e6c5") : ZTheme.color("#f48a9b");
                    ctx.beginPath();
                    ctx.moveTo(splitX, middle);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                }
            }
            root.points.forEach(p => {
                if (p.delta === null || p.delta === undefined)
                    return;
                ctx.fillStyle = p.delta >= 0 ? ZTheme.color("#62e6c5") : ZTheme.color("#f48a9b");
                ctx.beginPath();
                ctx.arc(root.sx(p), root.sy(p), 2.5, 0, Math.PI * 2);
                ctx.fill();
            });
        }
    }
    Rectangle {
        visible: root.selected >= 0
        x: root.selected >= 0 ? root.sx(root.points[root.selected]) : 0
        y: 18
        width: 1
        height: parent.height - 48
        color: ZTheme.color("#6488a7")
    }
    MouseArea {
        id: tracker
        anchors.fill: parent
        hoverEnabled: true
        onPositionChanged: mouse => {
            let best = -1, distance = 25;
            root.points.forEach((p, i) => {
                let d = Math.abs(root.sx(p) - mouse.x);
                if (d < distance) {
                    distance = d;
                    best = i;
                }
            });
            root.selected = best;
        }
        onExited: root.selected = -1
        ToolTip.visible: root.selected >= 0
        ToolTip.text: root.selected >= 0 ? root.time(root.points[root.selected].timestamp) + " · " + (root.points[root.selected].delta === null ? "Or non disponible" : root.points[root.selected].delta + " PO d’écart") : ""
    }
    ZText {
        anchors.centerIn: parent
        visible: root.points.length === 0
        text: "La courbe n’est pas disponible pour cette partie."
        color: ZTheme.color("#a6b9cb")
        width: parent.width - 80
        horizontalAlignment: Text.AlignHCenter
    }
}
