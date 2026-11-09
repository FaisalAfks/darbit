// What every moving part of a page shares (#441): when the page was last shown, and each card's turn in the rise that
// follows, so a page's cards rise one after another without knowing about each other.
.pragma library

var FRESH_MS = 1500     // a card made this soon after its page shows (its data just came) rises with the others
var BURST_MS = 60       // cards asking for a turn this close together are one page's rise
var MOST_TURNS = 8      // no card waits longer than this many turns, however long the page

var shownAt = 0
var turnsAt = 0
var turns = 0

function pageShown() {
    shownAt = Date.now()
}

function fresh() {
    return Date.now() - shownAt < FRESH_MS
}

// the next card's place in the rise: 0, 1, 2... for the cards of one page shown at once
function nextTurn() {
    var now = Date.now()
    if (now - turnsAt > BURST_MS) turns = 0
    turnsAt = now
    var turn = Math.min(turns, MOST_TURNS)
    turns += 1
    return turn
}
