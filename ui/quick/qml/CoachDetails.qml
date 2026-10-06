import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root
    property var sections: []
    property string version: ""
    signal momentSelected(int seconds)
    spacing: 14
    ZText {
        text: "Revoir les moments de la partie"
        font.pixelSize: 22
        font.weight: Font.DemiBold
        Layout.topMargin: 10
    }
    Repeater {
        model: root.sections
        Surface {
            id: section
            required property var modelData
            required property int index
            property bool expanded: false
            Layout.fillWidth: true
            implicitHeight: body.implicitHeight + 40
            ColumnLayout {
                id: body
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                    margins: 20
                }
                spacing: 14
                RowLayout {
                    Layout.fillWidth: true
                    ZText {
                        text: section.modelData.title
                        font.pixelSize: 19
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    ZButton {
                        objectName: "coachGroup" + section.index
                        text: (section.expanded ? "Réduire" : "Ouvrir") + " · " + section.modelData.events.length + " moments"
                        onClicked: section.expanded = !section.expanded
                    }
                }
                ZText {
                    text: section.modelData.status + " · " + section.modelData.summary
                    color: ZTheme.color("#a6bfd3")
                    Layout.fillWidth: true
                }
                Repeater {
                    model: section.expanded ? section.modelData.events : []
                    Surface {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: eventBody.implicitHeight + 32
                        ColumnLayout {
                            id: eventBody
                            anchors {
                                top: parent.top
                                left: parent.left
                                right: parent.right
                                margins: 16
                            }
                            spacing: 12
                            RowLayout {
                                Layout.fillWidth: true
                                ZText {
                                    text: modelData.title
                                    font.pixelSize: 17
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                }
                                ZButton {
                                    visible: modelData.seconds !== null
                                    text: "Voir " + modelData.time + " →"
                                    onClicked: root.momentSelected(modelData.seconds)
                                }
                            }
                            ZText {
                                visible: modelData.subtitle !== ""
                                text: modelData.subtitle
                                color: ZTheme.color("#a6bfd3")
                                Layout.fillWidth: true
                            }
                            Flow {
                                Layout.fillWidth: true
                                spacing: 5
                                Repeater {
                                    model: modelData.items
                                    Portrait {
                                        required property var modelData
                                        kind: "item"
                                        identity: String(modelData)
                                        version: root.version
                                        width: 30
                                    }
                                }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: width > 900 ? 3 : 2
                                columnSpacing: 18
                                rowSpacing: 12
                                Repeater {
                                    model: modelData.metrics
                                    ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        ZText {
                                            text: modelData.label
                                            color: ZTheme.color("#95acc3")
                                            font.pixelSize: 11
                                            Layout.fillWidth: true
                                        }
                                        ZText {
                                            text: modelData.value
                                            font.pixelSize: 14
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }
                            Repeater {
                                model: modelData.context
                                ZText {
                                    required property string modelData
                                    text: "• " + modelData
                                    color: ZTheme.color("#a6bfd3")
                                    font.pixelSize: 12
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
