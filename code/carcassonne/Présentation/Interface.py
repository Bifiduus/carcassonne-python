class GameCLI:
    def __init__(self, game):
        self.game = game
        self.running = True

    def run(self):
        print("Bienvenue dans Carcassonne")
        print("Tapez 'help' pour la liste des commandes.\n")

        while self.running:
            try:
                input("> ").strip()
                
            except KeyboardInterrupt:
                print("\nFin de partie.")
                self.running = False