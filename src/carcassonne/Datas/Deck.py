class Deck:
    def __init__(self):
        self.tiles = [
            "FFFF/m", "FFFF/m", "FFFF/m", "FFFF/m",
            "FFFR/m", "FFFR/m",
            "CFFF", "CFFF", "CFFF", "CFFF", "CFFF",
            "FCFC/f", "FCFC/f", "FCFC/f",
            "CFCF/c",
            "CFCF/b", "CFCF/b",
            "CCCC/b",
            "FFCC", "FFCC",
            "CCFF", "CCFF", "CCFF",
            "CCFF/b", "CCFF/b",
            "CCCF", "CCCF", "CCCF",
            "CCCF/b",
            "CCCR",
            "CCCR/b", "CCCR/b",
            "FRFR", "FRFR", "FRFR", "FRFR", "FRFR", "FRFR", "FRFR", "FRFR",
            "FFRR", "FFRR", "FFRR", "FFRR", "FFRR", "FFRR", "FFRR", "FFRR", "FFRR",
            "CRFR", "CRFR", "CRFR", "CRFR",
            "CFRR", "CFRR", "CFRR",
            "CRRF", "CRRF", "CRRF",
            "CCRR", "CCRR", "CCRR",
            "CCRR/b", "CCRR/b",
            "FRRR", "FRRR", "FRRR", "FRRR",
            "CRRR", "CRRR", "CRRR",
            "RRRR",
            "FSRS/m",
            "FFSF", "FFSF",
            "FSFS", "FSFS",
            "FFSS", "FFSS",
            "CSCS",
            "CCSS",
            "CSRS",
            "RSRS",
            "RRSS",
        ]
        
    def draw(self):
        if not self.tiles:
            print("Deck is empty, cannot draw a tile.")
            return None
        return self.tiles.pop()