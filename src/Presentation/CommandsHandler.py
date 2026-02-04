class GameCLI:
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.running = True

    def handle_command(self, command, player):
        
        if command == "help":
            self.show_help()
        elif command == "status":
            self.show_status(player)
        elif command.startswith("place "):
            self.p(command[6:], player)
        elif command.startswith("meeple "):
            self.place_meeple(command[7:], player)
        elif command == "end":
            self.end_turn(player)
        else:
            print("Commande inconnue. Tapez 'help' pour la liste des commandes.")
        def show_help(self):
            print("Commandes disponibles:")
            print("  help          - Affiche cette aide")
            print("  status        - Affiche le statut actuel du jeu")
            print("  place <args>  - Place une tuile avec les arguments spécifiés")
            print("  meeple <args> - Place un meeple avec les arguments spécifiés")
            print("  end           - Termine le tour actuel")