// The Library: every picture, point and area of the bot, by group, with its last match score; missing ones first.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Flickable {
    id: page
    property string filter: "all"  // all, risky, missing
    contentHeight: column.height + 120
    clip: true
    ScrollBar.vertical: ScrollBar {}

    readonly property var shown: studio.library.filter(function (asset) {
        if (filter === "missing") return asset.missing
        if (filter === "risky") return page.risky(asset)
        return true
    })
    readonly property var groups: {
        var found = [], index = {}
        for (var at = 0; at < shown.length; at++) {
            var asset = shown[at], name = asset.group || "Other"
            if (!(name in index)) { index[name] = found.length; found.push({ name: name, assets: [] }) }
            found[index[name]].assets.push(asset)
        }
        return found
    }

    function score(asset) {
        return asset.scores && asset.scores.length ? asset.scores[asset.scores.length - 1] : null
    }
    function risky(asset) {
        var last = score(asset)
        return last !== null && last < (asset.similarity || 0.9) + 0.05
    }
    function count(kind) {
        return studio.library.filter(function (asset) {
            return kind === "missing" ? asset.missing : kind === "risky" ? page.risky(asset) : true
        }).length
    }

    ColumnLayout {
        id: column
        x: 24; width: page.width - 48
        spacing: 20

        RowLayout {
            spacing: 16
            Text { text: "Library"; color: studio.colors.text; font.pixelSize: 30; font.weight: Font.Bold }
            Pill {
                height: 40
                Tab { height: 30; label: "All " + page.count("all"); current: page.filter === "all"; onClicked: page.filter = "all" }
                Tab { height: 30; label: "Risky " + page.count("risky"); current: page.filter === "risky"; onClicked: page.filter = "risky" }
                Tab { height: 30; label: "Missing " + page.count("missing"); current: page.filter === "missing"; onClicked: page.filter = "missing" }
            }
        }

        Text {
            visible: page.groups.length === 0
            text: studio.library.length === 0 ? "No pictures yet: capture them with darbit Studio's Capture, or put PNGs in the bot's images folder."
                : "Nothing here."
            color: studio.colors.muted; font.pixelSize: 15
        }

        Repeater {
            model: page.groups
            delegate: Glass {
                required property var modelData
                title: modelData.name
                note: modelData.assets.length + (modelData.assets.length === 1 ? " picture" : " pictures")
                Layout.fillWidth: true
                Layout.preferredHeight: 70 + grid.height
                content: Flow {
                    id: grid
                    width: parent.width
                    spacing: 14
                    Repeater {
                        model: modelData.assets
                        delegate: Rectangle {
                            required property var modelData
                            width: 150; height: 150; radius: 14
                            color: studio.colors.raised
                            border.color: modelData.missing ? studio.colors.danger : "transparent"
                            Rectangle {
                                x: 10; y: 10; width: 130; height: 100; radius: 10
                                color: studio.colors.bg
                                clip: true
                                Image {
                                    anchors.fill: parent
                                    source: modelData.thumbnail || ""
                                    fillMode: Image.PreserveAspectFit
                                    asynchronous: true
                                }
                                Text {
                                    visible: !modelData.thumbnail
                                    anchors.centerIn: parent
                                    text: modelData.missing ? "missing" : modelData.kind
                                    color: modelData.missing ? studio.colors.danger : studio.colors.muted
                                }
                            }
                            RowLayout {
                                x: 10; y: 118; width: 130
                                Text {
                                    text: modelData.name
                                    color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold
                                    elide: Text.ElideMiddle; Layout.fillWidth: true
                                }
                                Chip {
                                    visible: page.score(modelData) !== null
                                    height: 20
                                    text: page.score(modelData) !== null ? page.score(modelData).toFixed(2) : ""
                                    tone: page.risky(modelData) ? "warn" : "ok"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
