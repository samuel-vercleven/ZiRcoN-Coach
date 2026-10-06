import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    property var connection: ({})
    property bool pendingNotes: false
    readonly property bool accountChangeAllowed: !pendingNotes || accountField.text.trim().toLowerCase() === String(connection.riotId || "").toLowerCase()
    signal noteRequested
    spacing: 20
    Connections {
        target: coach
        function onCredentialSaved() {
            keyField.clear();
        }
    }
    Surface {
        Layout.fillWidth: true
        implicitHeight: form.implicitHeight + 48
        ColumnLayout {
            id: form
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 24
            }
            spacing: 14
            ZText {
                text: "Ton compte Riot"
                font.pixelSize: 25
                font.weight: Font.DemiBold
            }
            ZText {
                text: "Compte EUW · La clé reste sur cet ordinateur. Elle n’apparaît jamais dans les analyses."
                color: ZTheme.color("#a6bfd3")
                Layout.fillWidth: true
            }
            ZText {
                text: root.connection.keyStatus || "Connexion à configurer"
                color: ZTheme.color("#75e7d0")
            }
            GridLayout {
                Layout.fillWidth: true
                columns: width > 900 ? 2 : 1
                columnSpacing: 18
                rowSpacing: 10
                ColumnLayout {
                    Layout.fillWidth: true
                    ZText {
                        text: "Identifiant Riot"
                        color: ZTheme.color("#a6bfd3")
                    }
                    ZField {
                        id: accountField
                        objectName: "accountField"
                        Layout.fillWidth: true
                        placeholderText: "Pseudo#TAG"
                        text: root.connection.riotId || ""
                        enabled: !coach.operation.working
                        Accessible.name: "Identifiant Riot"
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    ZText {
                        text: "Parties à importer"
                        color: ZTheme.color("#a6bfd3")
                    }
                    ZSelect {
                        id: scopeField
                        Layout.fillWidth: true
                        model: ["20 dernières", "50 dernières", "100 dernières"]
                        currentIndex: Math.max(0, [20, 50, 100].indexOf(root.connection.scope || 20))
                        enabled: !coach.operation.working
                    }
                }
            }
            ZText {
                text: "Clé d’accès Riot"
                color: ZTheme.color("#a6bfd3")
            }
            ZField {
                id: keyField
                objectName: "keyField"
                Layout.fillWidth: true
                echoMode: TextInput.Password
                placeholderText: root.connection.keySaved ? "Une clé est enregistrée. Colle ici une nouvelle clé pour la remplacer." : "Colle ta clé Riot ici"
                enabled: !coach.operation.working
                Accessible.name: "Clé Riot masquée"
            }
            Flow {
                Layout.fillWidth: true
                spacing: 10
                ZButton {
                    text: "Enregistrer le compte"
                    enabled: !coach.operation.working && root.accountChangeAllowed
                    onClicked: coach.saveAccount(accountField.text, [20, 50, 100][scopeField.currentIndex])
                }
                ZButton {
                    text: "Vérifier la clé"
                    enabled: !coach.operation.working
                    onClicked: coach.validateKey(keyField.text, accountField.text, [20, 50, 100][scopeField.currentIndex], false)
                }
                ZButton {
                    text: "Vérifier et enregistrer"
                    primary: true
                    enabled: !coach.operation.working && root.accountChangeAllowed
                    onClicked: coach.validateKey(keyField.text, accountField.text, [20, 50, 100][scopeField.currentIndex], true)
                }
                ZButton {
                    text: "Portail Riot ↗"
                    onClicked: Qt.openUrlExternally("https://developer.riotgames.com/")
                }
            }
            ZText {
                text: "Une clé personnelle peut expirer : remplace-la ici si Riot refuse l’import. Aucune clé n’est livrée avec l’application."
                color: ZTheme.color("#94adc2")
                font.pixelSize: 12
                Layout.fillWidth: true
            }
            ZButton {
                visible: root.pendingNotes && !root.accountChangeAllowed
                text: "Enregistre d’abord ta note avant de changer de compte"
                onClicked: root.noteRequested()
            }
        }
    }
    Surface {
        Layout.fillWidth: true
        implicitHeight: localData.implicitHeight + 48
        ColumnLayout {
            id: localData
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 24
            }
            spacing: 14
            ZText {
                text: "Tes données, sur ton PC"
                font.pixelSize: 23
                font.weight: Font.DemiBold
            }
            GridLayout {
                Layout.fillWidth: true
                columns: width > 800 ? 3 : 2
                columnSpacing: 24
                rowSpacing: 18
                Repeater {
                    model: [
                        {
                            label: "Parties enregistrées",
                            value: root.connection.matches || 0
                        },
                        {
                            label: "Détails de partie",
                            value: root.connection.timelines || 0
                        },
                        {
                            label: "Parties analysées",
                            value: root.connection.analysed || 0
                        },
                        {
                            label: "Dernière partie",
                            value: root.connection.latest || "—"
                        },
                        {
                            label: "Dernier import",
                            value: root.connection.lastSync || "—"
                        },
                        {
                            label: "Clé enregistrée",
                            value: root.connection.keySaved ? "Oui" : "Non"
                        }
                    ]
                    ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        ZText {
                            text: modelData.label
                            color: ZTheme.color("#95acc3")
                            font.pixelSize: 12
                            Layout.fillWidth: true
                        }
                        ZText {
                            text: String(modelData.value)
                            font.pixelSize: 17
                            Layout.fillWidth: true
                        }
                    }
                }
            }
            ZButton {
                text: "Importer mes parties"
                primary: true
                enabled: !coach.operation.working
                onClicked: coach.importMatches()
            }
        }
    }
    Surface {
        Layout.fillWidth: true
        implicitHeight: about.implicitHeight + 40
        ZText {
            id: about
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 20
            }
            color: ZTheme.color("#a6bfd3")
            font.pixelSize: 12
            text: "ZiRcoN Coach · Analyse après-match · SoloQ EUW\nLes conseils servent à revoir tes décisions et tester une habitude, pas à prouver une cause du résultat.\nZiRcoN Coach n’est pas affilié à Riot Games. Riot Games et League of Legends sont des marques de Riot Games."
        }
    }
}
