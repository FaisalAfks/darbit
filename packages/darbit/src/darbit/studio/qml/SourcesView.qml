// The Gains by source block's body (Block.qml): one currency's gains today split by where they came from, then the
// week as stacked bars. Loaded only when the block is on the Overview.
import QtQuick
import QtQuick.Layouts
import "format.js" as Format
import "motion.js" as Motion

Column {
    id: split
    required property var block  // the Block it's drawn in: its info and tone()
    width: parent ? parent.width : 0; spacing: 6
    readonly property var sources: block.info.sources || []
    readonly property var today: block.info.today || []
    readonly property real todayTotal: today.reduce(function (sum, one) { return sum + one }, 0)
    readonly property real most: Math.max.apply(null, today.concat([1]))
    readonly property var week: block.info.week || []
    readonly property var weekTotals: week.map(function (amounts) { return amounts.reduce(function (sum, one) { return sum + one }, 0) })
    readonly property real weekMost: Math.max.apply(null, weekTotals.concat([1]))
    Text { visible: split.todayTotal === 0; text: "Nothing gained yet today."; color: studio.colors.faint; font.pixelSize: 13 }
    Bar {
        visible: split.todayTotal > 0
        width: split.width; height: 14; radius: 5
        shares: split.today.map(function (one) { return one / Math.max(1, split.todayTotal) })
        tints: split.sources.map(function (one, index) { return block.tone(index) })
    }
    Item { width: 1; height: 2 }
    Repeater {
        model: split.sources.length
        delegate: RowLayout {
            required property int index
            visible: split.today[index] > 0
            width: split.width; height: 24; spacing: 12
            Text {
                Layout.preferredWidth: Math.min(120, split.width * 0.3); elide: Text.ElideRight
                text: split.sources[index]; color: studio.colors.text; font.pixelSize: 13
            }
            Bar { Layout.fillWidth: true; height: 8; radius: 4; share: split.today[index] / split.most; tint: block.tone(index) }
            Text {
                Layout.preferredWidth: 72; horizontalAlignment: Text.AlignRight
                text: "+" + Format.compact(split.today[index]); color: studio.colors.muted; font.pixelSize: 13
            }
        }
    }
    Text {
        topPadding: 10
        text: "THIS WEEK"; color: studio.colors.muted
        font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3
    }
    Row {
        id: days
        width: split.width; height: 64; spacing: 6
        Repeater {
            model: split.week.length
            delegate: Item {
                id: day
                required property int index
                readonly property var amounts: split.week[index] || []
                readonly property real total: split.weekTotals[index] || 0
                // the top part with something in it, rounded at its top
                readonly property int topPart: {
                    for (var at = amounts.length - 1; at >= 0; at--) if (amounts[at] > 0) return at
                    return -1
                }
                anchors.bottom: parent.bottom
                width: (days.width - 6 * 6) / 7
                height: Math.max(3, 60 * total / split.weekMost)
                // the day's bar grows from the bottom when the page shows, one after another, as a chart's
                property real grown: 1
                transform: Scale { origin.y: day.height; yScale: day.grown }
                function grow() {
                    if (!studio.motion.on) { growing.stop(); grown = 1; return }
                    grown = 0
                    growing.wait = studio.motion.growDelay + index * studio.motion.growStagger
                    growing.restart()
                }
                onVisibleChanged: if (visible) grow(); else { growing.stop(); grown = 1 }
                Component.onCompleted: if (Motion.fresh()) grow()
                SequentialAnimation {
                    id: growing
                    property int wait: 0
                    PauseAnimation { duration: growing.wait }
                    NumberAnimation { target: day; property: "grown"; to: 1; duration: studio.motion.grow; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.spring }
                }
                Rectangle {  // a day with nothing: a stub, as on a chart
                    visible: day.total === 0
                    anchors.bottom: parent.bottom; width: parent.width; height: 3; radius: 1.5; color: studio.colors.raised
                }
                Column {  // the first source at the bottom, as in the bar above read from the left
                    anchors.bottom: parent.bottom; width: parent.width
                    Repeater {
                        model: day.amounts.length
                        delegate: Rectangle {
                            required property int index
                            readonly property int part: day.amounts.length - 1 - index
                            width: day.width
                            height: day.total > 0 ? day.height * day.amounts[part] / day.total : 0
                            color: block.tone(part)
                            opacity: day.index === split.week.length - 1 ? 1 : 0.85  // today the brightest
                            topLeftRadius: part === day.topPart ? 4 : 0; topRightRadius: topLeftRadius
                        }
                    }
                }
            }
        }
    }
}
