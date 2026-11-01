// The Library: every picture, point and area of the bot as cards with their last score against the similarity they
// need; one toolbar to search, filter, sort and group; an inspector that slides in for the chosen one.
// The cards sit in rows of a ListView, so only the rows on screen are made, however big the library.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: page
    property string kind: "all"     // all, image, region, location
    property bool missingOnly: false
    property bool weakOnly: false
    property string sort: "name"    // name, score, uses
    property string group: "none"   // none, name, kind
    property string query: ""
    property string chosen: ""
    readonly property var chosenAsset: onActions ? null : find(chosen)
    readonly property var chosenAction: onActions ? findAction(chosen) : null
    function findAction(name) {
        for (var index = 0; index < studio.actions.length; index++)
            if (studio.actions[index].name === name) return studio.actions[index]
        return null
    }
    readonly property int cardWidth: 176
    readonly property int columns: Math.max(1, Math.floor((grid.width + 14) / (cardWidth + 14)))

    function score(asset) { return asset.scores && asset.scores.length ? asset.scores[asset.scores.length - 1] : null }
    function needs(asset) { return asset.similarity || 0.9 }
    function weak(asset) { var last = score(asset); return last !== null && last < needs(asset) + 0.05 }
    function find(name) {
        for (var index = 0; index < studio.library.length; index++)
            if (studio.library[index].name === name) return studio.library[index]
        return null
    }
    function count(test) { return studio.library.filter(test).length }
    function kindLabel(kind) { return kind === "region" ? "area" : kind === "location" ? "point" : kind }

    readonly property bool onActions: kind === "action"
    readonly property var shown: {
        var words = query.toLowerCase()
        if (onActions)
            return studio.actions.filter(function (action) { return words === "" || action.name.toLowerCase().indexOf(words) >= 0 })
        var found = studio.library.filter(function (asset) {
            if (kind !== "all" && asset.kind !== kind) return false
            if (missingOnly && !asset.missing) return false
            if (weakOnly && !page.weak(asset)) return false
            return words === "" || asset.name.toLowerCase().indexOf(words) >= 0
        })
        found.sort(function (a, b) {
            if (sort === "score") return (page.score(a) === null ? 2 : page.score(a)) - (page.score(b) === null ? 2 : page.score(b))
            if (sort === "uses") return (b.uses || 0) - (a.uses || 0)
            return a.name.localeCompare(b.name)
        })
        return found
    }
    // the shown assets as rows of cards, each row tagged with its group (for the list's section headers)
    readonly property var rows: {
        var groups = [], index = {}
        for (var at = 0; at < shown.length; at++) {
            var asset = shown[at]
            var name = page.onActions ? "" : group === "name" ? (asset.name.indexOf(".") > 0 ? asset.name.split(".")[0] : "Other")
                : group === "kind" ? page.kindLabel(asset.kind) + "s" : ""
            if (!(name in index)) { index[name] = groups.length; groups.push({ name: name, assets: [] }) }
            groups[index[name]].assets.push(asset)
        }
        if (group === "name" || group === "kind") groups.sort(function (a, b) { return a.name.localeCompare(b.name) })
        var found = []
        for (var g = 0; g < groups.length; g++)
            for (var start = 0; start < groups[g].assets.length; start += columns)
                found.push({ group: groups[g].name + " · " + groups[g].assets.length, assets: groups[g].assets.slice(start, start + columns) })
        return found
    }

    // ---- the toolbar
    RowLayout {
        id: tools
        x: 24; width: page.width - 48
        spacing: 10
        TextField {
            id: search
            Layout.preferredWidth: window.narrow ? 170 : 240; Layout.preferredHeight: 42
            placeholderText: "Search " + studio.library.length + " assets"
            placeholderTextColor: studio.colors.faint
            color: studio.colors.text; font.pixelSize: 14
            leftPadding: 38
            onTextChanged: page.query = text
            background: Rectangle {
                radius: 21; color: studio.colors.glass; border.color: search.activeFocus ? studio.colors.accent : studio.colors.line
                Text { x: 15; anchors.verticalCenter: parent.verticalCenter; text: "⌕"; color: studio.colors.faint; font.pixelSize: 16; font.family: studio.symbols }
            }
        }
        Segmented {
            itemHeight: 34
            current: page.kind
            model: [
                { key: "all", label: "All", count: studio.library.length },
                { key: "image", label: "Images", count: page.count(function (a) { return a.kind === "image" }) },
                { key: "region", label: "Areas", count: page.count(function (a) { return a.kind === "region" }) },
                { key: "location", label: "Points", count: page.count(function (a) { return a.kind === "location" }) },
                { key: "action", label: "Actions", count: studio.actions.length }
            ]
            onPicked: function (key) { page.kind = key; page.chosen = "" }
        }
        // shown while there's something to filter for (or the filter is on)
        Toggle {
            readonly property int many: page.count(function (a) { return a.missing })
            visible: many > 0 || on
            text: "Missing " + many; tone: "danger"; on: page.missingOnly; onClicked: page.missingOnly = !page.missingOnly
        }
        Toggle {
            readonly property int many: page.count(page.weak)
            visible: many > 0 || on
            text: "Weak " + many; tone: "warn"; on: page.weakOnly; onClicked: page.weakOnly = !page.weakOnly
        }
        Item { Layout.fillWidth: true }
        PillButton {
            id: viewButton
            icon: "⇅"; text: window.narrow ? "" : (page.sort === "name" ? "Name" : page.sort === "score" ? "Weakest" : "Most used") + (page.group !== "none" ? " · by " + page.group : "")
            kind: "quiet"
            onClicked: viewMenu.open()
            Popup {
                id: viewMenu
                y: viewButton.height + 8; x: viewButton.width - width
                width: 230; padding: 8
                background: Rectangle { radius: 14; color: studio.colors.glassStrong; border.color: studio.colors.line }
                contentItem: Column {
                    spacing: 2
                    Text { text: "SORT"; color: studio.colors.faint; font.pixelSize: 11; font.letterSpacing: 1.3; leftPadding: 12; topPadding: 4; bottomPadding: 4 }
                    MenuLine { width: 214; icon: page.sort === "name" ? "✓" : ""; text: "By name"; onClicked: page.sort = "name" }
                    MenuLine { width: 214; icon: page.sort === "score" ? "✓" : ""; text: "Weakest first"; onClicked: page.sort = "score" }
                    MenuLine { width: 214; icon: page.sort === "uses" ? "✓" : ""; text: "Most used first"; onClicked: page.sort = "uses" }
                    Text { text: "GROUP"; color: studio.colors.faint; font.pixelSize: 11; font.letterSpacing: 1.3; leftPadding: 12; topPadding: 8; bottomPadding: 4 }
                    MenuLine { width: 214; icon: page.group === "none" ? "✓" : ""; text: "No groups"; onClicked: page.group = "none" }
                    MenuLine { width: 214; icon: page.group === "name" ? "✓" : ""; text: "By the first part of the name"; onClicked: page.group = "name" }
                    MenuLine { width: 214; icon: page.group === "kind" ? "✓" : ""; text: "By kind"; onClicked: page.group = "kind" }
                }
            }
        }
        // on a narrow window the tools on the right show only their icons
        PillButton { icon: "◎"; text: window.narrow ? "" : "Highlight"; onClicked: studio.toggleHighlight() }
        PillButton { icon: "●"; text: window.narrow ? "" : "Record"; onClicked: window.recordAction("") }
        PillButton { kind: "primary"; icon: "▣"; text: window.narrow ? "" : "Capture"; onClicked: studio.openCapture("any") }
    }

    // ---- the cards
    ListView {
        id: grid
        anchors { left: parent.left; leftMargin: 24; top: tools.bottom; topMargin: 18; bottom: parent.bottom
                  right: parent.right; rightMargin: inspector.open ? inspector.width + 40 : 24 }
        clip: true
        spacing: 14
        boundsBehavior: Flickable.StopAtBounds
        cacheBuffer: 400
        model: page.rows
        ScrollBar.vertical: ScrollBar {}
        section.property: page.group === "none" ? "" : "group"
        section.delegate: Text {
            required property string section
            text: section.toUpperCase()
            color: studio.colors.muted; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3
            topPadding: 8; bottomPadding: 10
        }
        delegate: Row {
            required property var modelData
            spacing: 14
            Repeater {
                model: page.onActions ? modelData.assets : []
                delegate: ActionCard {
                    required property var modelData
                    width: page.cardWidth
                    action: modelData
                    chosen: page.chosen === modelData.name
                    dimmed: page.chosen !== "" && !chosen
                    onClicked: page.chosen = chosen ? "" : modelData.name
                    onPlay: studio.playAction(modelData.name)
                }
            }
            Repeater {
                model: page.onActions ? [] : modelData.assets
                delegate: AssetCard {
                    required property var modelData
                    width: page.cardWidth
                    asset: modelData
                    score: page.score(modelData)
                    needs: page.needs(modelData)
                    weak: page.weak(modelData)
                    chosen: page.chosen === modelData.name
                    dimmed: page.chosen !== "" && !chosen
                    onClicked: { page.chosen = chosen ? "" : modelData.name; if (page.chosen) studio.loadUses(page.chosen) }
                }
            }
        }
        Column {
            visible: page.shown.length === 0
            anchors.centerIn: parent
            spacing: 14
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: page.onActions ? (studio.actions.length === 0 ? "No actions yet" : "Nothing matches")
                    : !studio.libraryReady ? "Loading the pictures…"
                    : studio.library.length === 0 ? "No pictures yet" : "Nothing matches"
                color: studio.colors.text; font.pixelSize: 20; font.weight: Font.Bold
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: page.onActions || studio.libraryReady
                text: page.onActions ? (studio.actions.length === 0 ? "Record one: every key, click and mouse move, played back the same." : "Clear the search.")
                    : studio.library.length === 0 ? "Capture one from the game's screen, or put PNGs in the bot's images folder." : "Clear the search or the filters."
                color: studio.colors.muted; font.pixelSize: 14
            }
            PillButton {
                visible: page.onActions ? studio.actions.length === 0 : studio.libraryReady && studio.library.length === 0
                anchors.horizontalCenter: parent.horizontalCenter; kind: "primary"
                icon: page.onActions ? "●" : "▣"; text: page.onActions ? "Record" : "Capture"
                onClicked: page.onActions ? window.recordAction("") : studio.openCapture("any")
            }
        }
    }

    // ---- the inspector
    Inspector {
        id: inspector
        readonly property bool open: page.chosenAsset !== null || page.chosenAction !== null
        anchors { top: tools.bottom; topMargin: 18; bottom: parent.bottom; bottomMargin: 24 }
        width: 330
        x: open ? page.width - width - 24 : page.width + 10
        Behavior on x { NumberAnimation { duration: studio.effects ? 260 : 0; easing.type: Easing.OutCubic } }
        asset: page.chosenAsset
        action: page.chosenAction
        score: page.chosenAsset ? page.score(page.chosenAsset) : null
        needs: page.chosenAsset ? page.needs(page.chosenAsset) : 0.9
        kindLabel: page.chosenAsset ? page.kindLabel(page.chosenAsset.kind) : ""
        onClosed: page.chosen = ""
        onRenamed: function (to) {
            if (page.onActions) studio.renameAction(page.chosen, to)
            else studio.renameAsset(page.chosen, to)
            page.chosen = to
        }
        onDeleted: {
            if (page.onActions) studio.deleteAction(page.chosen)
            else studio.deleteAsset(page.chosen)
            page.chosen = ""
        }
    }
    Shortcut { sequence: "Esc"; enabled: page.chosen !== "" && page.visible; onActivated: page.chosen = "" }
    Shortcut { sequence: "Ctrl+F"; enabled: page.visible; onActivated: search.forceActiveFocus() }
}
