import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    objectName: "quickWindow"
    width: 1600
    height: 960
    minimumWidth: 1120
    minimumHeight: 720
    visible: true
    title: ZTheme.belveth ? "ZiRcoN Coach · Bel’Veth" : "ZiRcoN Coach · Nouvelle interface"
    readonly property bool belvethMode: ZTheme.belveth
    color: ZTheme.color("#09131f")
    property string page: "home"
    property int matchTab: 0
    property var dashboard: coach ? coach.state : ({
            player: {},
            count: 0,
            metrics: [],
            matches: [],
            champions: []
        })
    property var game: coach ? coach.detail : ({})
    property var build: coach ? coach.build : ({})
    property string query: ""
    property string resultFilter: "ALL"
    property string roleFilter: "ALL"
    property string patchFilter: "ALL"
    property bool favoritesOnly: false
    property int selectedMoment: -1
    property bool allowDiscard: false
    Connections {
        target: coach
        function onSettingsRequested() {
            window.page = "settings";
        }
        function onRefreshed() {
            if (window.page === "match")
                window.page = "history";
        }
    }
    onClosing: close => {
        if (coach && coach.operation.working) {
            close.accepted = false;
            waitDialog.open();
        } else if (notesPanel.hasDrafts && !allowDiscard) {
            close.accepted = false;
            noteDialog.open();
        }
    }
    Dialog {
        id: noteDialog
        width: 450
        implicitWidth: 450
        anchors.centerIn: parent
        title: "Une note n’est pas enregistrée"
        modal: true
        background: Rectangle { radius: 16; color: ZTheme.color("#152638"); border.color: ZTheme.color("#30485d") }
        header: ZText { text: noteDialog.title; font.pixelSize: 18; font.weight: Font.DemiBold; padding: 18 }
        contentItem: ColumnLayout {
            ZText {
                text: "Enregistre ta note avant de quitter si tu veux la retrouver à la prochaine ouverture."
                Layout.fillWidth: true
            }
            ZButton {
                text: "Revenir à la note"
                onClicked: {
                    noteDialog.close();
                    window.openMatch(notesPanel.lastDraft);
                    window.matchTab = 4;
                }
            }
            ZButton {
                objectName: "discardDraftButton"
                text: "Quitter sans enregistrer"
                onClicked: {
                    window.allowDiscard = true;
                    noteDialog.close();
                    window.close();
                }
            }
        }
    }
    Dialog {
        id: waitDialog
        width: 420
        implicitWidth: 420
        anchors.centerIn: parent
        title: "Opération en cours"
        modal: true
        standardButtons: Dialog.Ok
        background: Rectangle { radius: 16; color: ZTheme.color("#152638"); border.color: ZTheme.color("#30485d") }
        header: ZText { text: waitDialog.title; font.pixelSize: 18; font.weight: Font.DemiBold; padding: 18 }
        contentItem: ZText {
            text: "Attends la fin de la demande avant de fermer ZiRcoN, pour préserver l’import en cours."
            width: 350
        }
    }
    property bool reduceMotion: false
    property bool buildReasonsExpanded: false
    function shortReasons(reasons) {
        if (reasons.length <= 3)
            return reasons;
        const selected = reasons.slice(-2).concat(reasons.slice(0, 1));
        return selected.filter((value, index) => selected.indexOf(value) === index);
    }
    function openMatch(id) {
        if (coach.openMatch(id)) {
            matchTab = 0;
            selectedMoment = -1;
            buildReasonsExpanded = false;
            page = "match";
            detailScroll.contentItem.contentY = 0;
        }
    }
    function asset(name) {
        if (name === "zircon" && ZTheme.belveth)
            name = "zircon-void";
        return resourceRoot + "/" + name + ".svg";
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop {
                position: 0
                color: ZTheme.color("#0d1928")
            }
            GradientStop {
                position: 0.65
                color: ZTheme.color("#101f30")
            }
            GradientStop {
                position: 1
                color: ZTheme.color("#12192b")
            }
        }
    }
    Rectangle {
        x: parent.width - 250
        y: -160
        width: 490
        height: 490
        radius: 245
        color: ZTheme.color("#101a7381")
    }
    Rectangle {
        x: 350
        y: parent.height - 190
        width: 540
        height: 540
        radius: 270
        color: ZTheme.color("#0a8170a8")
    }

    Rectangle {
        id: sidebar
        width: 188
        height: parent.height
        color: ZTheme.color("#09121e")
        Rectangle {
            anchors.right: parent.right
            height: parent.height
            width: 1
            color: ZTheme.color("#27384a")
        }
        Row {
            x: 22
            y: 30
            spacing: 10
            Image {
                width: 35
                height: 35
                source: window.asset("zircon")
            }
            Column {
                spacing: 4
                ZText {
                    text: "ZiRcoN"
                    font.pixelSize: 21
                    font.bold: true
                }
                ZText {
                    text: "COACH"
                    font.pixelSize: 9
                    font.letterSpacing: 3
                    color: ZTheme.color("#74c6c9")
                }
            }
        }
        ZText {
            x: 23
            y: 112
            text: "TON ESPACE"
            font.pixelSize: 10
            font.letterSpacing: 2
            color: ZTheme.color("#758ea7")
        }
        Column {
            x: 14
            y: 142
            width: parent.width - 28
            spacing: 10
            Repeater {
                model: [
                    {
                        label: "Vue d’ensemble",
                        name: "home",
                        icon: "nav-home"
                    },
                    {
                        label: "Mes parties",
                        name: "history",
                        icon: "nav-history"
                    },
                    {
                        label: "Progression",
                        name: "progress",
                        icon: "nav-progress"
                    },
                    {
                        label: "Réglages",
                        name: "settings",
                        icon: "nav-settings"
                    }
                ]
                AbstractButton {
                    required property var modelData
                    objectName: modelData.name + "Button"
                    width: parent.width
                    height: 52
                    hoverEnabled: true
                    Accessible.name: modelData.label
                    background: Rectangle {
                        radius: 13
                        color: window.page === modelData.name || (window.page === "match" && modelData.name === "history") ? ZTheme.color("#1e3549") : parent.hovered ? ZTheme.color("#132636") : "transparent"
                        Behavior on color {
                            ColorAnimation {
                                duration: 160
                            }
                        }
                        Rectangle {
                            visible: window.page === modelData.name || (window.page === "match" && modelData.name === "history")
                            x: 0
                            y: 17
                            height: 18
                            width: 3
                            radius: 2
                            color: ZTheme.color("#70ebcf")
                        }
                    }
                    contentItem: Row {
                        x: 13
                        spacing: 10
                        Image {
                            width: 21
                            height: 21
                            anchors.verticalCenter: parent.verticalCenter
                            source: window.asset(modelData.icon)
                        }
                        ZText {
                            text: modelData.label
                            anchors.verticalCenter: parent.verticalCenter
                            font.pixelSize: 13
                            color: ZTheme.color("#cad7e6")
                        }
                    }
                    onClicked: window.page = modelData.name
                }
            }
        }
        Column {
            x: 18
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 24
            width: parent.width - 36
            spacing: 10
            ZText {
                visible: window.height > 880
                text: "Une partie.\nUne chose à retenir."
                font.pixelSize: 15
                color: ZTheme.color("#c3d3e3")
                font.italic: true
                width: parent.width
            }
            ZButton {
                text: window.reduceMotion ? "Animations : coupées" : "Animations : actives"
                width: parent.width
                onClicked: window.reduceMotion = !window.reduceMotion
            }
            Row {
                width: parent.width
                spacing: 6
                ZButton {
                    objectName: "belvethThemeButton"
                    width: (parent.width - 6) / 2
                    height: 36
                    text: "Bel’Veth"
                    selected: ZTheme.belveth
                    onClicked: ZTheme.belveth = true
                }
                ZButton {
                    objectName: "turquoiseThemeButton"
                    width: (parent.width - 6) / 2
                    height: 36
                    text: "Turquoise"
                    selected: !ZTheme.belveth
                    onClicked: ZTheme.belveth = false
                }
            }
            ZText {
                text: "●  Données locales"
                color: ZTheme.color("#7ee4cb")
                font.pixelSize: 11
            }
        }
    }

    Item {
        id: workspace
        anchors {
            left: sidebar.right
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            leftMargin: 30
            rightMargin: 30
        }
        RowLayout {
            id: header
            width: parent.width
            height: 94
            ColumnLayout {
                spacing: 4
                Layout.fillWidth: true
                ZText {
                    text: window.page === "home" ? "L’après-match, autrement." : window.page === "history" ? "Tes parties" : window.page === "progress" ? "Ta progression" : window.page === "settings" ? "Tes réglages" : "Retour sur ta partie"
                    font.pixelSize: 24
                    font.weight: Font.DemiBold
                }
                ZText {
                    text: window.page === "match" ? "Le résultat est un point de départ. Le prochain réflexe, la suite." : dashboard.count + " parties locales · Classé solo / duo"
                    font.pixelSize: 12
                    color: ZTheme.color("#96adc5")
                }
            }
            ZButton {
                text: "Importer des parties"
                primary: true
                enabled: coach && !coach.operation.working
                onClicked: coach.importMatches()
            }
            Rectangle {
                width: 1
                height: 32
                color: ZTheme.color("#314356")
                Layout.leftMargin: 12
                Layout.rightMargin: 12
            }
            ColumnLayout {
                spacing: 3
                Layout.maximumWidth: 200
                Layout.preferredWidth: 200
                ZText {
                    text: dashboard.player.name || "Ton compte"
                    Layout.fillWidth: true
                    wrapMode: Text.NoWrap
                    elide: Text.ElideRight
                    font.weight: Font.DemiBold
                    font.pixelSize: 13
                }
                ZText {
                    text: (dashboard.player.rank || "Données locales") + (dashboard.player.lp && dashboard.player.lp !== "—" ? " · " + dashboard.player.lp : "")
                    Layout.fillWidth: true
                    wrapMode: Text.NoWrap
                    elide: Text.ElideRight
                    font.pixelSize: 11
                    color: ZTheme.color("#9db3c9")
                }
            }
        }

        Rectangle {
            id: feedback
            anchors.top: header.bottom
            width: parent.width
            height: coach && (coach.notice || coach.operation.working) ? 70 : 0
            visible: height > 0
            radius: 12
            color: ZTheme.color("#19393e")
            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12
                ZText {
                    text: coach ? (coach.operation.working ? coach.operation.text : coach.notice) : ""
                    Layout.fillWidth: true
                    font.pixelSize: 13
                }
                ZButton {
                    visible: coach && !coach.operation.working
                    text: "Fermer"
                    onClicked: coach.dismissNotice()
                }
            }
            Rectangle {
                visible: coach && coach.operation.working
                anchors.bottom: parent.bottom
                width: parent.width * (coach ? coach.operation.progress : 0) / 100
                height: 3
                color: ZTheme.color("#70ebcf")
            }
        }
        ScrollView {
            id: homeScroll
            anchors {
                top: feedback.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                bottomMargin: 20
            }
            visible: window.page === "home"
            opacity: visible ? 1 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: window.reduceMotion ? 0 : 220
                }
            }
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: homeScroll.availableWidth
                spacing: 20
                Surface {
                    Layout.fillWidth: true
                    implicitHeight: 264
                    tint: ZTheme.color("#183a4b")
                    clip: true
                    Rectangle {
                        x: parent.width - 320
                        y: -80
                        width: 440
                        height: 440
                        radius: 220
                        color: ZTheme.color("#10376379")
                        border.color: ZTheme.color("#355b70")
                        border.width: 1
                        rotation: 12
                    }
                    Rectangle {
                        x: parent.width - 265
                        y: -24
                        width: 330
                        height: 330
                        radius: 165
                        color: ZTheme.color("#13394a61")
                        border.color: ZTheme.color("#447d87")
                    }
                    Rectangle {
                        x: parent.width - 215
                        y: 27
                        width: 228
                        height: 228
                        radius: 114
                        color: ZTheme.color("#22456d78")
                        border.color: ZTheme.color("#5192a0")
                    }
                    Image {
                        x: parent.width - 170
                        y: 70
                        width: 132
                        height: 132
                        source: window.asset("zircon")
                        rotation: -10
                        SequentialAnimation on rotation {
                            running: homeScroll.visible && !window.reduceMotion
                            loops: Animation.Infinite
                            NumberAnimation {
                                from: -10
                                to: -2
                                duration: 6500
                                easing.type: Easing.InOutSine
                            }
                            NumberAnimation {
                                from: -2
                                to: -10
                                duration: 6500
                                easing.type: Easing.InOutSine
                            }
                        }
                    }
                    ColumnLayout {
                        x: 32
                        y: 28
                        width: parent.width - 360
                        spacing: 12
                        ZText {
                            text: ZTheme.belveth ? "APPRENDRE. S’ADAPTER. ÉVOLUER." : "LE PETIT DÉCLIC APRÈS LA GAME"
                            color: ZTheme.color("#75e7d0")
                            font.pixelSize: 11
                            font.letterSpacing: 2
                        }
                        ZText {
                            text: "Chaque partie.\nUn nouveau réflexe."
                            font.pixelSize: 39
                            font.weight: Font.DemiBold
                            lineHeight: 0.97
                            Layout.fillWidth: true
                        }
                        ZText {
                            text: "Revois les moments utiles, comprends tes achats\net repars avec une idée concrète à tester."
                            color: ZTheme.color("#b2c7d9")
                            Layout.fillWidth: true
                        }
                        ZButton {
                            text: dashboard.matches.length ? "Revoir ma dernière partie   →" : "Connecter mon compte   →"
                            primary: true
                            onClicked: dashboard.matches.length ? window.openMatch(dashboard.matches[0].id) : window.page = "settings"
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Repeater {
                        model: dashboard.metrics
                        Surface {
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: 128
                            Column {
                                x: 22
                                y: 18
                                width: parent.width - 44
                                spacing: 6
                                ZText {
                                    text: modelData.label
                                    color: ZTheme.color("#a4bad0")
                                    font.pixelSize: 12
                                }
                                ZText {
                                    text: modelData.value
                                    font.pixelSize: 30
                                    font.weight: Font.DemiBold
                                }
                                ZText {
                                    text: modelData.hint
                                    font.pixelSize: 11
                                    color: ZTheme.color("#8ca4bb")
                                    width: parent.width
                                }
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    ZText {
                        text: "Tes dernières parties"
                        font.pixelSize: 20
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    ZButton {
                        text: "Tout l’historique →"
                        onClicked: window.page = "history"
                    }
                }
                Repeater {
                    model: dashboard.matches.slice(0, 4)
                    delegate: matchRow
                }
                ZText {
                    visible: dashboard.matches.length === 0
                    text: "Ton historique est encore vide. Connecte ton compte dans Réglages pour importer tes parties."
                    color: ZTheme.color("#adc3d6")
                    Layout.fillWidth: true
                }
            }
        }

        ColumnLayout {
            anchors {
                top: feedback.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                bottomMargin: 18
            }
            visible: window.page === "history"
            opacity: visible ? 1 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: window.reduceMotion ? 0 : 220
                }
            }
            spacing: 18
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                TextField {
                    objectName: "matchSearch"
                    Layout.fillWidth: true
                    implicitHeight: 44
                    color: ZTheme.color("#edf3fa")
                    placeholderText: "Rechercher un champion, un rôle…"
                    placeholderTextColor: ZTheme.color("#8aa3bd")
                    font.family: "Segoe UI"
                    font.pixelSize: 14
                    leftPadding: 16
                    background: Rectangle {
                        radius: 12
                        color: ZTheme.color("#152638")
                        border.color: parent.activeFocus ? ZTheme.color("#65d8c5") : ZTheme.color("#30485d")
                    }
                    onTextChanged: window.query = text.toLowerCase()
                }
                Repeater {
                    model: [
                        {
                            text: "Toutes",
                            value: "ALL"
                        },
                        {
                            text: "Victoires",
                            value: "WIN"
                        },
                        {
                            text: "Défaites",
                            value: "LOSS"
                        }
                    ]
                    ZButton {
                        required property var modelData
                        text: modelData.text
                        selected: window.resultFilter === modelData.value
                        onClicked: window.resultFilter = modelData.value
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                ZSelect {
                    Layout.fillWidth: true
                    model: ["Tous les rôles"].concat(dashboard.roles || [])
                    onActivated: window.roleFilter = currentIndex === 0 ? "ALL" : currentText
                }
                ZSelect {
                    Layout.fillWidth: true
                    model: ["Tous les patchs"].concat(dashboard.patches || [])
                    onActivated: window.patchFilter = currentIndex === 0 ? "ALL" : currentText
                }
                ZButton {
                    text: window.favoritesOnly ? "★ Mes favoris" : "☆ Favoris"
                    selected: window.favoritesOnly
                    onClicked: window.favoritesOnly = !window.favoritesOnly
                }
            }
            ListView {
                id: historyList
                objectName: "historyList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 12
                model: dashboard.matches.filter(m => (window.resultFilter === "ALL" || m.result === window.resultFilter) && (window.roleFilter === "ALL" || m.role === window.roleFilter) && (window.patchFilter === "ALL" || m.patch === window.patchFilter) && (!window.favoritesOnly || m.starred) && (m.champion + " " + m.role).toLowerCase().includes(window.query))
                delegate: matchRow
                ScrollBar.vertical: ScrollBar {}
                ZText {
                    anchors.centerIn: parent
                    visible: historyList.count === 0
                    text: "Aucune partie ne correspond à cette recherche."
                    color: ZTheme.color("#a6bdd3")
                }
            }
        }

        ScrollView {
            id: progressScroll
            anchors {
                top: feedback.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                bottomMargin: 20
            }
            visible: window.page === "progress"
            clip: true
            contentWidth: availableWidth
            ProgressPage {
                width: progressScroll.availableWidth
                progress: coach ? coach.progressData : ({})
            }
        }

        ScrollView {
            id: settingsScroll
            anchors {
                top: feedback.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                bottomMargin: 20
            }
            visible: window.page === "settings"
            clip: true
            contentWidth: availableWidth
            SettingsPage {
                width: settingsScroll.availableWidth
                connection: dashboard.connection || ({})
                pendingNotes: notesPanel.hasDrafts
                onNoteRequested: {
                    window.openMatch(notesPanel.lastDraft);
                    window.matchTab = 4;
                }
            }
        }

        ScrollView {
            id: detailScroll
            objectName: "detailScroll"
            anchors {
                top: feedback.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                bottomMargin: 20
            }
            visible: window.page === "match"
            clip: true
            contentWidth: availableWidth
            opacity: visible ? 1 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: window.reduceMotion ? 0 : 220
                }
            }
            ColumnLayout {
                width: detailScroll.availableWidth
                spacing: 18
                Surface {
                    Layout.fillWidth: true
                    implicitHeight: 154
                    tint: game.result === "WIN" ? ZTheme.color("#1c3d45") : ZTheme.color("#2b2d43")
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 22
                        Portrait {
                            identity: game.champion || ""
                            version: game.version || ""
                            width: 98
                            radius: 18
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            ZText {
                                text: (game.resultText || "") + "  ·  " + (game.role || "")
                                font.pixelSize: 12
                                color: game.result === "WIN" ? ZTheme.color("#7de8cf") : ZTheme.color("#f4a2b4")
                                font.letterSpacing: 1
                            }
                            ZText {
                                text: game.champion || ""
                                font.pixelSize: 33
                                font.weight: Font.DemiBold
                            }
                            ZText {
                                text: (game.duration || "") + " · " + (game.date || "") + " · Patch " + (game.patch || "")
                                color: ZTheme.color("#a6bfd2")
                                font.pixelSize: 12
                            }
                        }
                        ColumnLayout {
                            spacing: 8
                            ZText {
                                text: game.kda || ""
                                font.pixelSize: 24
                                font.weight: Font.DemiBold
                            }
                            ZText {
                                text: (game.cs || "—") + " CS · " + (game.cspm || "—") + " / min"
                                color: ZTheme.color("#acc4d7")
                                font.pixelSize: 12
                            }
                        }
                        ColumnLayout {
                            spacing: 10
                            Layout.leftMargin: 12
                            ZText {
                                text: "BUILD FINAL"
                                color: ZTheme.color("#99b1c8")
                                font.pixelSize: 10
                                font.letterSpacing: 2
                            }
                            Row {
                                spacing: 5
                                Repeater {
                                    model: game.items || []
                                    Portrait {
                                        required property var modelData
                                        kind: "item"
                                        identity: String(modelData)
                                        version: game.version || ""
                                        width: window.width < 1350 ? 27 : 36
                                    }
                                }
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    ZButton {
                        text: "← Parties"
                        onClicked: window.page = "history"
                        Layout.rightMargin: 12
                    }
                    Repeater {
                        model: ["Résumé", "Coach", "Objets", "Déroulé", "Notes"]
                        ZButton {
                            required property string modelData
                            required property int index
                            objectName: "matchTab" + index
                            text: modelData
                            selected: window.matchTab === index
                            onClicked: window.matchTab = index
                        }
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                }
                RowLayout {
                    visible: window.matchTab === 0
                    Layout.fillWidth: true
                    spacing: 18
                    Layout.alignment: Qt.AlignTop
                    Surface {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 720
                        Layout.alignment: Qt.AlignTop
                        implicitHeight: teams.implicitHeight + 42
                        RowLayout {
                            id: teams
                            anchors {
                                top: parent.top
                                left: parent.left
                                right: parent.right
                                margins: 20
                            }
                            spacing: 14
                            TeamList {
                                players: game.allies || []
                                version: game.version || ""
                                Layout.fillWidth: true
                                Layout.preferredWidth: 320
                                Layout.alignment: Qt.AlignTop
                            }
                            TeamList {
                                players: game.enemies || []
                                version: game.version || ""
                                enemy: true
                                Layout.fillWidth: true
                                Layout.preferredWidth: 320
                                Layout.alignment: Qt.AlignTop
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 410
                        Layout.alignment: Qt.AlignTop
                        spacing: 18
                        Surface {
                            Layout.fillWidth: true
                            implicitHeight: 302
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 18
                                spacing: 4
                                ZText {
                                    text: "Le fil de la partie"
                                    font.pixelSize: 19
                                    font.weight: Font.DemiBold
                                }
                                ZText {
                                    text: "Écart d’or des équipes · PO"
                                    color: ZTheme.color("#9fb7cf")
                                    font.pixelSize: 12
                                }
                                GoldChart {
                                    objectName: "goldChart"
                                    points: game.points || []
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                }
                                ZText {
                                    text: ZTheme.belveth ? "Doré : ton équipe devant · Rose : derrière" : "Vert : ton équipe devant · Rose : derrière"
                                    color: ZTheme.color("#aac1d6")
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                }
                            }
                        }
                        CoachFocus {
                            visible: (game.focuses || []).length > 0
                            coaching: (game.focuses || [])[0] || ({})
                            Layout.fillWidth: true
                        }
                        Surface {
                            visible: (game.focuses || []).length === 0
                            Layout.fillWidth: true
                            implicitHeight: noCoach.implicitHeight + 36
                            ZText {
                                id: noCoach
                                anchors {
                                    left: parent.left
                                    right: parent.right
                                    top: parent.top
                                    margins: 18
                                }
                                text: game.coachEmpty || "Pas assez d’informations pour un conseil fiable."
                                color: ZTheme.color("#a8c0d4")
                            }
                        }
                    }
                }
                ColumnLayout {
                    visible: window.matchTab === 1
                    Layout.fillWidth: true
                    spacing: 16
                    ZText {
                        text: "Une idée à tester, pas dix choses à corriger."
                        font.pixelSize: 25
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    ZText {
                        text: "Les conseils s’appuient uniquement sur les observations étayées de cette partie."
                        color: ZTheme.color("#9fb7ce")
                        Layout.fillWidth: true
                    }
                    Repeater {
                        model: game.focuses || []
                        CoachFocus {
                            required property var modelData
                            coaching: modelData
                            Layout.fillWidth: true
                        }
                    }
                    CoachDetails {
                        Layout.fillWidth: true
                        sections: game.sections || []
                        version: game.version || ""
                        onMomentSelected: seconds => {
                            window.selectedMoment = seconds;
                            window.matchTab = 3;
                            detailScroll.contentItem.contentY = 0;
                        }
                    }
                    ZText {
                        visible: (game.focuses || []).length === 0
                        text: game.coachEmpty || "Pas de conseil fiable disponible."
                        color: ZTheme.color("#b1c5d8")
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    visible: window.matchTab === 2
                    Layout.fillWidth: true
                    spacing: 18
                    Surface {
                        tint: ZTheme.color("#1a3940")
                        Layout.fillWidth: true
                        implicitHeight: buildContent.implicitHeight + 48
                        ColumnLayout {
                            id: buildContent
                            anchors {
                                top: parent.top
                                left: parent.left
                                right: parent.right
                                margins: 24
                            }
                            spacing: 16
                            ZText {
                                text: "Un achat adapté au contexte"
                                font.pixelSize: 25
                                font.weight: Font.DemiBold
                                Layout.fillWidth: true
                            }
                            ZText {
                                visible: coach && coach.busy
                                text: "J’examine les achats possibles et les adversaires à ce moment de la partie…"
                                color: ZTheme.color("#afc9d4")
                                Layout.fillWidth: true
                            }
                            ZText {
                                visible: coach && !coach.busy && build.status !== "SUPPORTED_HEURISTIC"
                                text: build.reason || "Je n’ai pas assez d’informations pour proposer un objet précis."
                                color: ZTheme.color("#bad0de")
                                Layout.fillWidth: true
                            }
                            ColumnLayout {
                                visible: coach && !coach.busy && build.status === "SUPPORTED_HEURISTIC"
                                Layout.fillWidth: true
                                spacing: 16
                                RowLayout {
                                    Portrait {
                                        kind: "item"
                                        identity: String(build.target_item || "")
                                        version: game.version || ""
                                        description: build.target_name || ""
                                        width: 74
                                        radius: 14
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        ZText {
                                            text: build.target_name || ""
                                            font.pixelSize: 27
                                            font.weight: Font.DemiBold
                                            Layout.fillWidth: true
                                        }
                                        ZText {
                                            text: "Contexte observé à " + (build.snapshot_label || "—") + " · Patch " + (build.patch || "—")
                                            color: ZTheme.color("#9fbfcd")
                                            Layout.fillWidth: true
                                        }
                                    }
                                    ColumnLayout {
                                        Gauge {
                                            value: build.score || 0
                                        }
                                        ZText {
                                            text: "Pertinence indicative"
                                            font.pixelSize: 10
                                            color: ZTheme.color("#a1c3ca")
                                        }
                                    }
                                }
                                Repeater {
                                    model: window.buildReasonsExpanded ? (build.reasons || []) : window.shortReasons(build.reasons || [])
                                    ZText {
                                        required property string modelData
                                        text: "•  " + modelData
                                        color: ZTheme.color("#c4d8e3")
                                        Layout.fillWidth: true
                                    }
                                }
                                ZButton {
                                    visible: (build.reasons || []).length > 3
                                    text: window.buildReasonsExpanded ? "Réduire les explications" : "Toutes les raisons du conseil"
                                    onClicked: window.buildReasonsExpanded = !window.buildReasonsExpanded
                                }
                                ZText {
                                    text: "Face aux adversaires observés à ce moment"
                                    font.pixelSize: 16
                                    font.weight: Font.DemiBold
                                }
                                Flow {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Repeater {
                                        model: build.enemy_snapshot || []
                                        Row {
                                            required property var modelData
                                            spacing: 7
                                            Portrait {
                                                identity: modelData.champion
                                                version: game.version || ""
                                                width: 36
                                            }
                                            ZText {
                                                text: modelData.champion + "\n" + (modelData.health_max === null ? "PV inconnus" : Math.round(modelData.health_max) + " PV") + " · armure " + (modelData.armor === null ? "—" : Math.round(modelData.armor))
                                                font.pixelSize: 11
                                                color: ZTheme.color("#a6c2d3")
                                            }
                                        }
                                    }
                                }
                                ZText {
                                    text: "Si tu retournais à la boutique à ce moment-là"
                                    font.pixelSize: 16
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                }
                                Repeater {
                                    model: build.buy_now_named || []
                                    RowLayout {
                                        required property var modelData
                                        Portrait {
                                            kind: "item"
                                            identity: String(modelData.item_id)
                                            version: game.version || ""
                                            description: modelData.name
                                            width: 34
                                        }
                                        ZText {
                                            text: modelData.name + " · " + modelData.cost + " PO à payer à ce moment"
                                            color: ZTheme.color("#b4cfdd")
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                                ZText {
                                    text: "Ce conseil est une piste contextuelle, pas un build optimal garanti. Il utilise les données de ce moment, pas l’inventaire final."
                                    color: ZTheme.color("#98b8c6")
                                    font.pixelSize: 12
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                    Repeater {
                        model: build.status === "SUPPORTED_HEURISTIC" ? (build.alternatives || []) : []
                        Surface {
                            id: alternativeCard
                            required property var modelData
                            property bool expanded: false
                            Layout.fillWidth: true
                            implicitHeight: alternative.implicitHeight + 36
                            RowLayout {
                                id: alternative
                                anchors {
                                    top: parent.top
                                    left: parent.left
                                    right: parent.right
                                    margins: 18
                                }
                                spacing: 16
                                Portrait {
                                    kind: "item"
                                    identity: String(modelData.item_id)
                                    version: game.version || ""
                                    description: modelData.name
                                    width: 46
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    ZText {
                                        text: "Autre piste · " + modelData.name
                                        font.pixelSize: 18
                                        font.weight: Font.DemiBold
                                        Layout.fillWidth: true
                                    }
                                    Repeater {
                                        model: alternativeCard.expanded ? (modelData.reasons || []) : (modelData.reasons || []).slice(0, 2)
                                        ZText {
                                            required property string modelData
                                            text: modelData
                                            color: ZTheme.color("#a2bdd2")
                                            font.pixelSize: 12
                                            Layout.fillWidth: true
                                        }
                                    }
                                    ZButton {
                                        visible: (modelData.reasons || []).length > 2
                                        text: alternativeCard.expanded ? "Réduire" : "Pourquoi cette autre piste ?"
                                        onClicked: alternativeCard.expanded = !alternativeCard.expanded
                                    }
                                }
                            }
                        }
                    }
                }
                ColumnLayout {
                    visible: window.matchTab === 3
                    Layout.fillWidth: true
                    spacing: 12
                    ZText {
                        text: "Les objectifs observés"
                        font.pixelSize: 25
                        font.weight: Font.DemiBold
                    }
                    ZText {
                        visible: window.selectedMoment >= 0
                        text: "Moment à revoir : " + Math.floor(window.selectedMoment / 60) + ":" + ("0" + window.selectedMoment % 60).slice(-2) + " · repère dans la partie, pas une preuve de causalité"
                        color: ZTheme.color("#75e7d0")
                        Layout.fillWidth: true
                    }
                    Surface {
                        Layout.fillWidth: true
                        implicitHeight: 282
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            ZText {
                                text: "Écart d’or des équipes · PO"
                                font.pixelSize: 18
                                font.weight: Font.DemiBold
                            }
                            GoldChart {
                                points: game.points || []
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                            }
                        }
                    }
                    ZText {
                        text: "Contexte d’équipe : ces événements ne sont pas, à eux seuls, des erreurs personnelles."
                        color: ZTheme.color("#a6bfd3")
                        Layout.fillWidth: true
                    }
                    Repeater {
                        model: game.events || []
                        Surface {
                            required property var modelData
                            Layout.fillWidth: true
                            implicitHeight: 62
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 18
                                ZText {
                                    text: modelData.time
                                    color: ZTheme.color("#75e0ca")
                                    Layout.preferredWidth: 68
                                }
                                ZText {
                                    text: modelData.label
                                    Layout.fillWidth: true
                                }
                                ZText {
                                    text: modelData.sideLabel || "Équipe non précisée"
                                    color: ZTheme.color("#97b2c9")
                                    font.pixelSize: 12
                                }
                            }
                        }
                    }
                    ZText {
                        visible: (game.events || []).length === 0
                        text: "Aucun objectif enregistré dans les données disponibles."
                        color: ZTheme.color("#a1b9d0")
                    }
                }
                NotesPage {
                    id: notesPanel
                    visible: window.matchTab === 4
                    game: window.game
                    Layout.fillWidth: true
                }
            }
        }
    }

    Component {
        id: matchRow
        Surface {
            id: card
            required property var modelData
            width: workspace.width
            Layout.fillWidth: true
            implicitHeight: 110
            height: implicitHeight
            tint: hover.hovered ? ZTheme.color("#20384a") : ZTheme.color("#162a3b")
            Behavior on tint {
                ColorAnimation {
                    duration: 160
                }
            }
            transform: Translate {
                y: hover.hovered && !window.reduceMotion ? -2 : 0
                Behavior on y {
                    NumberAnimation {
                        duration: 150
                        easing.type: Easing.OutCubic
                    }
                }
            }
            Accessible.name: modelData.champion + ", " + modelData.resultText + ", " + modelData.date
            Accessible.role: Accessible.Button
            Accessible.onPressAction: window.openMatch(modelData.id)
            activeFocusOnTab: true
            Keys.onReturnPressed: window.openMatch(modelData.id)
            Keys.onSpacePressed: window.openMatch(modelData.id)
            border.color: activeFocus ? ZTheme.color("#7ce8d5") : ZTheme.color("#304458")
            Rectangle {
                x: 1
                y: 25
                width: 3
                height: parent.height - 50
                radius: 2
                color: modelData.result === "WIN" ? ZTheme.color("#66e3c8") : modelData.result === "LOSS" ? ZTheme.color("#ef91a7") : ZTheme.color("#8daac4")
            }
            RowLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 16
                Portrait {
                    identity: modelData.champion
                    version: modelData.version
                    width: 62
                    radius: 12
                }
                ColumnLayout {
                    Layout.preferredWidth: 142
                    spacing: 4
                    ZText {
                        text: modelData.champion
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    ZText {
                        text: modelData.resultText + " · " + modelData.role
                        color: modelData.result === "WIN" ? ZTheme.color("#74dec9") : ZTheme.color("#ed9bb0")
                        font.pixelSize: 11
                    }
                    ZText {
                        text: modelData.duration + " · " + modelData.date.slice(5, 10)
                        color: ZTheme.color("#8fa9c2")
                        font.pixelSize: 11
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 130
                    spacing: 6
                    ZText {
                        text: modelData.kda
                        font.pixelSize: 18
                        font.weight: Font.DemiBold
                    }
                    ZText {
                        text: modelData.cs + " CS · " + modelData.cspm + " / min"
                        color: ZTheme.color("#9db8cf")
                        font.pixelSize: 11
                    }
                }
                Row {
                    spacing: 4
                    Repeater {
                        model: card.modelData.items
                        Portrait {
                            required property var modelData
                            kind: "item"
                            identity: String(modelData)
                            version: card.modelData.version
                            width: window.width < 1400 ? 26 : 33
                            radius: 5
                        }
                    }
                }
                Item {
                    Layout.fillWidth: true
                }
                Column {
                    spacing: 4
                    Row {
                        spacing: 3
                        Repeater {
                            model: card.modelData.allies || []
                            Portrait {
                                required property string modelData
                                identity: modelData
                                version: card.modelData.version
                                width: 25
                                radius: 4
                            }
                        }
                    }
                    Row {
                        spacing: 3
                        Repeater {
                            model: card.modelData.enemies || []
                            Portrait {
                                required property string modelData
                                identity: modelData
                                version: card.modelData.version
                                width: 25
                                radius: 4
                                border.color: ZTheme.color("#856273")
                            }
                        }
                    }
                }
                ZText {
                    text: "↗"
                    color: ZTheme.color("#71d7ca")
                    font.pixelSize: 23
                    Layout.leftMargin: 4
                }
            }
            HoverHandler {
                id: hover
                cursorShape: Qt.PointingHandCursor
            }
            TapHandler {
                onTapped: window.openMatch(modelData.id)
            }
        }
    }
}
