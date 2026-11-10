// A window, sheet or panel made the first time it's wanted and kept from then on, like PageFrame's pages: one never
// used costs the Studio no memory, and its file isn't even compiled before then. It's made once `wanted` turns true,
// or at once by make(), which returns it.
import QtQuick

Loader {
    property bool wanted: false
    active: false
    onWantedChanged: if (wanted) active = true
    Component.onCompleted: if (wanted) active = true
    onLoaded: studio.releaseWhenHidden(item)  // a window made now gives back its graphics memory while hidden too

    function make() {
        active = true
        return item
    }
}
