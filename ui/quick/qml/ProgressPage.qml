import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root
    property var progress: ({})
    spacing: 20
    RowLayout {
        Layout.fillWidth: true
        ZText {
            text: "Un repère sur tes habitudes"
            font.pixelSize: 22
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        ZSelect {
            objectName: "progressWindow"
            model: ["10 dernières", "20 dernières", "50 dernières", "Tout l’historique"]
            currentIndex: 1
            onActivated: coach.setProgressWindow([10, 20, 50, 0][currentIndex])
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 14
        Repeater {
            model: root.progress.metrics || []
            Surface {
                required property var modelData
                Layout.fillWidth: true
                implicitHeight: 116
                Column {
                    x: 20
                    y: 18
                    spacing: 12
                    ZText {
                        text: modelData.label
                        font.pixelSize: 12
                        color: ZTheme.color("#95acc3")
                    }
                    ZText {
                        text: modelData.value
                        font.pixelSize: 29
                        font.weight: Font.DemiBold
                    }
                }
            }
        }
    }
    ZText {
        text: root.progress.comparison || ""
        color: ZTheme.color("#a6bfd3")
        Layout.fillWidth: true
    }
    ZText {
        text: "Ordre des parties : des anciennes aux récentes. Survole un point pour lire sa valeur. Les espaces indiquent des informations manquantes."
        color: ZTheme.color("#94adc2")
        font.pixelSize: 12
        Layout.fillWidth: true
    }
    GridLayout {
        Layout.fillWidth: true
        columns: width > 1100 ? 3 : 1
        columnSpacing: 16
        rowSpacing: 16
        Repeater {
            model: [
                {
                    title: "Victoires récentes",
                    note: "Pourcentage sur jusqu’à 5 parties à chaque point.",
                    values: root.progress.victories || [],
                    unit: "%",
                    maximum: 100
                },
                {
                    title: "Farm par minute",
                    note: "CS par minute pour chaque partie ; compare selon le rôle.",
                    values: root.progress.farm || [],
                    unit: "CS/min",
                    maximum: 0
                },
                {
                    title: "Morts par partie",
                    note: "Nombre observé, pas un jugement sur tes décisions.",
                    values: root.progress.deaths || [],
                    unit: "morts",
                    maximum: 0
                }
            ]
            Surface {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 350
                implicitHeight: 314
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 6
                    ZText {
                        text: modelData.title
                        font.pixelSize: 19
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    ZText {
                        text: modelData.note
                        color: ZTheme.color("#94adc2")
                        font.pixelSize: 12
                        Layout.fillWidth: true
                    }
                    TrendPlot {
                        values: modelData.values
                        labels: root.progress.labels || []
                        unit: modelData.unit
                        fixedMaximum: modelData.maximum
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                }
            }
        }
    }
    Surface {
        Layout.fillWidth: true
        implicitHeight: pool.implicitHeight + 48
        ColumnLayout {
            id: pool
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 24
            }
            spacing: 16
            ZText {
                text: "Les champions que tu joues"
                font.pixelSize: 22
                font.weight: Font.DemiBold
            }
            ZText {
                text: "La barre indique le nombre de parties, pas une note de performance."
                font.pixelSize: 12
                color: ZTheme.color("#94adc2")
                Layout.fillWidth: true
            }
            Repeater {
                model: root.progress.champions || []
                RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 14
                    Portrait {
                        identity: modelData.champion
                        width: 40
                    }
                    ZText {
                        text: modelData.champion
                        Layout.preferredWidth: 126
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        height: 10
                        radius: 5
                        color: ZTheme.color("#233a4c")
                        Rectangle {
                            height: parent.height
                            width: parent.width * modelData.games / Math.max(1, ...(root.progress.champions || []).map(c => c.games))
                            radius: 5
                            color: ZTheme.color("#76e7cf")
                        }
                    }
                    ZText {
                        text: modelData.games + " parties"
                        Layout.preferredWidth: 80
                        font.pixelSize: 12
                    }
                    ZText {
                        text: modelData.rate + " victoires"
                        Layout.preferredWidth: 132
                        font.pixelSize: 12
                        color: ZTheme.color("#78e4ce")
                    }
                }
            }
        }
    }
}
