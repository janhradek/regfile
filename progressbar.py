def progressbar(pc,size=15,empty="-",done="=",edges="[]",markfmt=" {}% ",markafter=False):
    """draw nice progressbars
    [ 5% ------------]
    [====== 50% -----]
    [========== 100% ]
    pc - percent amount thus expecting a number in range(0,101)
    size - total progress bar size in characters including everything (defaults to 15)
    empty - a character to print in empty progress space (defaults to "-")
    done - a character to print in done progress space (defaults to "=")
    edges - a two character string to print on the edges (defaults to "[]")
    markfmt - a marker format string (defaults to " {}% ")
    markafter - if True dont print mark at the exact spot but at the end (defaults to False)
    """
    assert(len(edges) == 2 or len(edges) == 0)
    assert(len(empty) == 1)
    assert(len(done) == 1)
    if len(edges) == 2:
        size-= 2 # - parentheses
    pcs = markfmt.format(pc)
    ticks = 1 + size - len(pcs) # one tick is (100/ticks) percent
    if markafter:
        pcs = pcs.strip()
        ticks = size = size - ( len(pcs) + 1 )
        ticks = size
    # done ticks
    td = ticks * pc / 100.0
    td = int(td)
    if td == ticks and not markafter:
        td -= 1
    pb = ""
    if td > 0:
        pb = td*done
    if not markafter:
        pb += pcs
    pb += empty*(size - len(pb))
    if len(edges) == 2:
        pb = edges[0] + pb + edges[1]
    if markafter:
        pb += " " + pcs
    return  pb


if __name__ == "__main__":

    print(progressbar(50,size=15))
    print()
    for i in range(0,101):
        print("\r"+progressbar(i,size=22,markfmt=""), end="")
        import time
        time.sleep(0.05)
    print()

