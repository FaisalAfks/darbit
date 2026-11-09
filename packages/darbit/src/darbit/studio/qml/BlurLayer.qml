// The blur a page gets while it blurs through (PageFrame, a setting): its layer's effect, made only once the setting
// is on, so the effects module is loaded only then. It blurs as much as the page's `blur` says.
import QtQuick
import QtQuick.Effects

MultiEffect {
    blurEnabled: true
    blurMax: 32
    blur: parent && parent.blur !== undefined ? parent.blur : 0
}
