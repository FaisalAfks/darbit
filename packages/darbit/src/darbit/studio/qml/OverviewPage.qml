// The Overview (round 14, C): what needs you, then the bot's blocks in rows of 12. The bot's author lays out the
// default (overview.toml) and adds blocks of their own (d.show, @d.block); Customize lets you drag blocks around, make
// them wider or narrower, take them off and add any from the gallery, kept for this bot; ↺ goes back to the bot's.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Flickable {
    id: page
    SmoothWheel { view: page }
    contentHeight: column.height + 60
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    interactive: !editing
    ScrollBar.vertical: ScrollBar {}

    property bool editing: false
    property bool galleryOpen: false
    readonly property var board: studio.overview || ({})
    readonly property var layout: board.layout || []
    readonly property var data: board.data || ({})
    readonly property var catalog: board.catalog || []
    readonly property var now: data.now || null
    readonly property var setup: data.setup || null
    readonly property var failures: data.failures || null
    readonly property bool empty: studio.bots.length === 0
    readonly property bool running: studio.bot.status === "running" || studio.bot.status === "paused"
    readonly property var lastFailure: failures && failures.items && failures.items.length ? failures.items[failures.items.length - 1] : null
    readonly property real gap: 16
    readonly property real unit: (column.width - 11 * gap) / 12
    // the layout as rows: blocks in order, a new row when the next one doesn't fit in what's left of 12
    readonly property var rows: {
        var found = [], row = [], used = 0
        for (var index = 0; index < layout.length; index++) {
            var width = layout[index].width || 4
            if (used + width > 12 && row.length) { found.push(row); row = []; used = 0 }
            row.push({ spec: layout[index], index: index })
            used += width
        }
        if (row.length) found.push(row)
        return found
    }
    readonly property var addable: catalog.filter(function (one) {
        return !layout.some(function (mine) { return mine.kind === one.kind && mine.shows === one.shows })
    })

    function widthOf(units) { return unit * units + gap * (units - 1) }
    function save(next) { studio.saveLayout(next) }
    function moveTo(from, sceneX, sceneY) {
        // the block dropped on: the one whose place holds the drop point; dropped elsewhere, it goes back
        var target = -1
        for (var at = 0; at < blocks.count; at++) {
            var other = blocks.itemAt(at)
            if (!other) continue
            var corner = other.mapToItem(null, 0, 0)
            if (sceneX >= corner.x && sceneX <= corner.x + other.width && sceneY >= corner.y && sceneY <= corner.y + other.height && other.index !== from)
                target = other.index
        }
        var next = layout.slice()
        if (target >= 0) {
            var moved = next.splice(from, 1)[0]
            next.splice(target, 0, moved)
        }
        save(next)
    }
    function resize(index, width) {
        var next = layout.slice()
        next[index] = Object.assign({}, next[index], { width: width })
        save(next)
    }
    function remove(index) { var next = layout.slice(); next.splice(index, 1); save(next) }
    function add(spec) { save(layout.concat([{ kind: spec.kind, shows: spec.shows, title: spec.title, width: spec.width, origin: spec.origin }])) }

    ColumnLayout {
        id: column
        x: 24; width: page.width - 48 - (page.galleryOpen ? gallery.width + 16 : 0)
        Behavior on width { NumberAnimation { duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic } }
        spacing: 16

        // ---- the first time: no bots yet
        Glass {
            visible: page.empty
            Layout.fillWidth: true; Layout.preferredHeight: 300
            padding: 34
            content: Item {
                anchors.fill: parent
                Image {
                    id: mark
                    source: "../logo.png"; width: 120; height: 120; sourceSize: Qt.size(240, 240); smooth: true
                    anchors.verticalCenter: parent.verticalCenter
                }
                Column {
                    anchors { left: mark.right; leftMargin: 34; right: parent.right; verticalCenter: parent.verticalCenter }
                    spacing: 12
                    Text { text: "WELCOME TO DARBIT"; color: studio.colors.accent; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3 }
                    Text { text: "Make your first bot"; color: studio.colors.text; font.pixelSize: 32; font.weight: Font.Bold }
                    Text {
                        width: parent.width
                        text: "A bot is a folder of plain Python and the images it looks for. Start one from the template, install one from its git link, or add a folder you already have."
                        color: studio.colors.muted; font.pixelSize: 14; wrapMode: Text.WordWrap
                    }
                    Item { width: 1; height: 6 }
                    Row {
                        spacing: 10
                        PillButton { kind: "primary"; icon: "+"; text: "New bot"; onClicked: window.newBot("new") }
                        PillButton { icon: "↓"; text: "From a git link"; onClicked: window.newBot("link") }
                        PillButton { kind: "quiet"; text: "Add a folder"; onClicked: window.newBot("folder") }
                    }
                }
            }
        }

        // ---- the toolbar: Customize, and while customizing, Done, Add and back to the bot's layout
        RowLayout {
            visible: !page.empty
            Layout.fillWidth: true
            spacing: 8
            Text {
                visible: !!page.board.problem
                Layout.fillWidth: true; elide: Text.ElideRight
                text: "overview.toml: " + (page.board.problem || "") + " (darbit's layout is shown)"
                color: studio.colors.warn; font.pixelSize: 12
            }
            Item { Layout.fillWidth: true; visible: !page.board.problem }
            PillButton { visible: !page.editing; kind: "quiet"; small: true; icon: "✎"; text: "Customize"; onClicked: page.editing = true }
            PillButton { visible: page.editing; small: true; icon: "+"; text: "Add a block"; onClicked: page.galleryOpen = !page.galleryOpen }
            PillButton { visible: page.editing && !!page.board.custom; small: true; kind: "quiet"; icon: "↺"; text: "The bot's layout"; onClicked: studio.resetLayout() }
            PillButton { visible: page.editing; small: true; kind: "primary"; text: "Done"; onClicked: { page.editing = false; page.galleryOpen = false } }
        }

        // ---- what needs you
        Banner {
            visible: page.running && page.now !== null && !!page.now.locked
            Layout.fillWidth: true
            tone: "warn"; icon: "⏸"
            title: "The screen is locked: the bot is waiting until it's back"
            detail: page.now && page.now.locked ? "since " + Format.clock(page.now.locked) + ". Nothing it sees or presses reaches the game while Windows is locked." : ""
        }
        Banner {
            readonly property int missing: page.setup && page.setup.total ? page.setup.total - page.setup.done : 0
            visible: missing > 0
            Layout.fillWidth: true
            tone: "info"; icon: "▣"
            title: missing + (missing === 1 ? " image in the setup guide isn't" : " images in the setup guide aren't") + " taken yet"
            detail: "The bot runs without them and skips what needs them." + (page.setup && page.setup.current ? " Next: " + page.setup.current.name + " on " + page.setup.current.screen : "")
            action: "Take them"
            onActed: studio.openCapture("guide")
        }
        Banner {
            visible: page.lastFailure !== null
            Layout.fillWidth: true
            tone: "danger"; icon: "!"
            title: page.lastFailure ? page.lastFailure.step + ": " + (page.lastFailure.reason || "failed") : ""
            detail: page.lastFailure ? "at " + Format.clock(page.lastFailure.time) + (page.failures.items.length > 1 ? " · " + page.failures.items.length + " problems today" : "") : ""
            action: "Why it stopped"
            onActed: window.go("results")
        }

        // ---- the blocks, row by row
        Text {
            visible: !page.empty && page.layout.length === 0
            text: page.editing ? "Add blocks from the gallery." : "No blocks: Customize to add some."
            color: studio.colors.muted; font.pixelSize: 14
        }
        Repeater {
            model: page.rows
            delegate: Row {
                id: row
                required property var modelData
                spacing: page.gap
                // the row as tall as its tallest block, so the cards line up
                readonly property real tallest: {
                    var most = 0
                    for (var at = 0; at < children.length; at++) most = Math.max(most, children[at].implicitHeight || 0)
                    return most
                }
                Repeater {
                    model: row.modelData
                    delegate: Block {
                        required property var modelData
                        readonly property int index: modelData.index
                        width: page.widthOf(modelData.spec.width || 4); height: row.tallest
                        spec: modelData.spec
                        info: page.data[modelData.spec.shows] === undefined ? null : page.data[modelData.spec.shows]
                        editing: page.editing
                        unit: page.unit; gap: page.gap
                        delay: index * 30
                        onMoved: function (x, y) { page.moveTo(index, x, y) }
                        onResized: function (width) { page.resize(index, width) }
                        onRemoved: page.remove(index)
                        Component.onCompleted: blocks.add(this)
                        Component.onDestruction: blocks.drop(this)
                    }
                }
            }
        }
    }
    // every block on the page, to find the one a block is dropped on
    QtObject {
        id: blocks
        property var items: []
        readonly property int count: items.length
        function add(item) { items = items.concat([item]) }
        function drop(item) { items = items.filter(function (one) { return one !== item }) }
        function itemAt(at) { return items[at] }
    }

    // ---- the gallery: every block this bot can show and isn't showing
    Glass {
        id: gallery
        visible: page.galleryOpen
        parent: page
        anchors { right: parent.right; rightMargin: 24; top: parent.top; topMargin: 12; bottom: parent.bottom; bottomMargin: 24 }
        width: 270
        title: "Add a block"
        lift: false
        content: Flickable {
            id: galleryList
            anchors.fill: parent
            contentHeight: choices.height; clip: true
            SmoothWheel { view: galleryList }
            Column {
                id: choices
                width: parent.width; spacing: 6
                Text { visible: page.addable.length === 0; width: parent.width; wrapMode: Text.Wrap; text: "Every block is on the Overview."; color: studio.colors.muted; font.pixelSize: 13 }
                Repeater {
                    model: page.addable
                    delegate: MenuLine {
                        required property var modelData
                        width: choices.width
                        icon: modelData.kind === "ring" ? "◔" : modelData.kind === "chart" ? "▁▃▅" : modelData.kind === "list" ? "≡" : modelData.kind === "button" ? "▶"
                            : modelData.kind === "screen" ? "▢" : modelData.kind === "number" ? "#" : "◆"
                        iconColor: modelData.origin && modelData.origin !== "darbit" ? studio.colors.slotBot : studio.colors.accent
                        text: modelData.title
                        detail: modelData.kind + (modelData.origin && modelData.origin !== "darbit" ? " · from " + modelData.origin : "")
                        onClicked: page.add(modelData)
                    }
                }
            }
        }
    }
}
