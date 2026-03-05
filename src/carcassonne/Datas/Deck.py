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
            "CRFR", "CRFR", "CRFR",
            #"CRFR",
            "CFRR", "CFRR", "CFRR",
            "CRRF", "CRRF", "CRRF",
            "CCRR", "CCRR", "CCRR",
            "CCRR/b", "CCRR/b",
            "FRRR", "FRRR", "FRRR", "FRRR",
            "CRRR", "CRRR", "CRRR",
            "RRRR",
            #"FSRS/m",
            #"FFSF", "FFSF",
            #"FSFS", "FSFS",
            #"FFSS", "FFSS",
            #"CSCS",
            #"CCSS",
            #"CSRS",
            #"RSRS",
            #"RRSS",
        ]
        
    def draw(self) -> str | None:
        if not self.tiles:
            print("Deck is empty, cannot draw a tile.")
            return None
        return self.tiles.pop()

    def len(self) -> int:
        return len(self.tiles)
    
    def shuffle_fisher_yates(self, seed: int | str) -> None:
        seed = [int(s) for s in str(seed)]
        seed_index = 0
        for i in range(len(self.tiles) - 1, 0, -1):
            if(seed_index + 1 < len(seed)):
                j = int(str(seed[seed_index]) + str(seed[seed_index + 1])) * 123 % (i + 1)
                seed_index += 1
            else:
                j = int(str(seed[seed_index]) + str(seed[0])) * 123 % (i + 1)
                seed_index = 0
            self.tiles[i], self.tiles[j] = self.tiles[j], self.tiles[i]

    def shuffle_naive(self, seed: int | str) -> None:
        seed = [int(s) for s in str(seed)]
        seed_index = 0
        n = len(self.tiles)
        for i in range(n):
            if(seed_index + 1 < len(seed)):
                j = int(str(seed[seed_index]) + str(seed[seed_index + 1])) * 123 % n
                seed_index += 1
            else:
                j = int(str(seed[seed_index]) + str(seed[0])) * 123 % n
                seed_index = 0
            self.tiles[i], self.tiles[j] = self.tiles[j], self.tiles[i]
