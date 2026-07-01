"""
Pseudo-code de logique robotique pour le tri de pieces rouges et bleues.

Objectif :
- recevoir les detections vision ;
- suivre les pieces sur un convoyeur en mouvement ;
- choisir une piece saisissable ;
- piloter le robot vers la prise ;
- deposer la piece dans le bac correspondant a sa couleur ;
- gerer les erreurs simples sans bloquer la production.
"""

from enum import Enum


class EtatRobot(Enum):
    INITIALISATION = "initialisation"
    ATTENTE_PIECE = "attente_piece"
    SUIVI_PIECE = "suivi_piece"
    PRISE = "prise"
    DEPOT = "depot"
    RETOUR = "retour"
    ERREUR = "erreur"


class Couleur(Enum):
    ROUGE = "rouge"
    BLEU = "bleu"


class Piece:
    def __init__(self, identifiant, x, y, orientation, couleur, timestamp_detection):
        self.identifiant = identifiant
        self.x = x
        self.y = y
        self.orientation = orientation
        self.couleur = couleur
        self.timestamp_detection = timestamp_detection
        self.deja_traitee = False


class LogiqueRobotique:
    def __init__(self, robot, vision, convoyeur, gripper, interface_operateur):
        self.robot = robot
        self.vision = vision
        self.convoyeur = convoyeur
        self.gripper = gripper
        self.interface_operateur = interface_operateur

        self.etat = EtatRobot.INITIALISATION
        self.file_pieces = []
        self.piece_courante = None

        self.compteur_rouge = 0
        self.compteur_bleu = 0
        self.compteur_defauts = 0

    def boucle_principale(self):
        while production_active():
            self.mettre_a_jour_detections_vision()
            self.supprimer_pieces_non_saisissables()

            if self.etat == EtatRobot.INITIALISATION:
                self.initialiser_cellule()

            elif self.etat == EtatRobot.ATTENTE_PIECE:
                self.selectionner_piece_a_prendre()

            elif self.etat == EtatRobot.SUIVI_PIECE:
                self.suivre_piece_sur_convoyeur()

            elif self.etat == EtatRobot.PRISE:
                self.prendre_piece()

            elif self.etat == EtatRobot.DEPOT:
                self.deposer_piece()

            elif self.etat == EtatRobot.RETOUR:
                self.retour_position_attente()

            elif self.etat == EtatRobot.ERREUR:
                self.gerer_erreur()

            self.mettre_a_jour_interface()

    def initialiser_cellule(self):
        if not self.robot.est_pret():
            self.robot.initialiser()

        if not self.gripper.est_pret():
            self.gripper.initialiser()

        if not self.vision.est_active():
            self.vision.demarrer_acquisition()

        self.robot.aller_position_attente()
        self.etat = EtatRobot.ATTENTE_PIECE

    def mettre_a_jour_detections_vision(self):
        detections = self.vision.lire_detections()

        for detection in detections:
            piece = Piece(
                identifiant=detection.id,
                x=detection.x,
                y=detection.y,
                orientation=detection.orientation,
                couleur=detection.couleur,
                timestamp_detection=detection.timestamp,
            )

            if self.piece_est_valide(piece):
                self.file_pieces.append(piece)

    def piece_est_valide(self, piece):
        if piece.couleur not in [Couleur.ROUGE, Couleur.BLEU]:
            return False

        if piece_trop_proche_d_une_autre(piece, self.file_pieces):
            return False

        if orientation_hors_limite(piece.orientation):
            return False

        return True

    def supprimer_pieces_non_saisissables(self):
        pieces_saisissables = []

        for piece in self.file_pieces:
            position_actuelle = self.calculer_position_piece(piece)

            if position_dans_zone_de_prise(position_actuelle):
                pieces_saisissables.append(piece)
            elif piece_sortie_de_la_zone_robot(position_actuelle):
                self.compteur_defauts += 1
                self.interface_operateur.signaler_defaut(
                    "Piece sortie de la zone robot avant prise"
                )

        self.file_pieces = pieces_saisissables

    def selectionner_piece_a_prendre(self):
        if not self.file_pieces:
            return

        self.piece_courante = choisir_piece_prioritaire(self.file_pieces)
        self.etat = EtatRobot.SUIVI_PIECE

    def suivre_piece_sur_convoyeur(self):
        position_piece = self.calculer_position_piece(self.piece_courante)

        if not position_dans_zone_de_prise(position_piece):
            self.compteur_defauts += 1
            self.piece_courante.deja_traitee = True
            self.etat = EtatRobot.ATTENTE_PIECE
            return

        point_prise = calculer_point_de_prise(
            position_piece,
            self.piece_courante.orientation,
        )

        self.robot.preparer_trajectoire_prise(point_prise)

        if self.robot.est_pret_pour_prise(point_prise):
            self.etat = EtatRobot.PRISE

    def prendre_piece(self):
        position_piece = self.calculer_position_piece(self.piece_courante)
        point_prise = calculer_point_de_prise(
            position_piece,
            self.piece_courante.orientation,
        )

        self.robot.aller_au_point(point_prise)
        self.gripper.fermer_ou_activer()

        if self.gripper.piece_detectee():
            self.piece_courante.deja_traitee = True
            self.etat = EtatRobot.DEPOT
        else:
            self.compteur_defauts += 1
            self.interface_operateur.signaler_defaut("Echec de prise")
            self.piece_courante.deja_traitee = True
            self.etat = EtatRobot.RETOUR

    def deposer_piece(self):
        if self.piece_courante.couleur == Couleur.ROUGE:
            position_bac = position_bac_rouge()
        else:
            position_bac = position_bac_bleu()

        self.robot.aller_au_point(position_bac)
        self.gripper.ouvrir_ou_desactiver()

        if self.piece_courante.couleur == Couleur.ROUGE:
            self.compteur_rouge += 1
        else:
            self.compteur_bleu += 1

        self.etat = EtatRobot.RETOUR

    def retour_position_attente(self):
        self.robot.aller_position_attente()
        self.piece_courante = None
        self.file_pieces = [piece for piece in self.file_pieces if not piece.deja_traitee]
        self.etat = EtatRobot.ATTENTE_PIECE

    def gerer_erreur(self):
        self.robot.arret_securise()
        self.gripper.ouvrir_ou_desactiver()
        self.interface_operateur.signaler_defaut("Erreur robot necessitant intervention")

        if self.interface_operateur.demande_rearmement():
            self.etat = EtatRobot.INITIALISATION

    def calculer_position_piece(self, piece):
        distance_convoyeur = self.convoyeur.distance_parcourue_depuis(
            piece.timestamp_detection
        )

        return {
            "x": piece.x + distance_convoyeur,
            "y": piece.y,
            "orientation": piece.orientation,
        }

    def mettre_a_jour_interface(self):
        self.interface_operateur.afficher_etat(self.etat.value)
        self.interface_operateur.afficher_compteurs(
            rouges=self.compteur_rouge,
            bleues=self.compteur_bleu,
            defauts=self.compteur_defauts,
        )


# Fonctions abstraites utilisees dans le pseudo-code.
# Elles representent des choix d'implementation a definir avec le robot,
# la vision, le convoyeur et les contraintes client.


def production_active():
    pass


def piece_trop_proche_d_une_autre(piece, file_pieces):
    pass


def orientation_hors_limite(orientation):
    pass


def position_dans_zone_de_prise(position_piece):
    pass


def piece_sortie_de_la_zone_robot(position_piece):
    pass


def choisir_piece_prioritaire(file_pieces):
    pass


def calculer_point_de_prise(position_piece, orientation):
    pass


def position_bac_rouge():
    pass


def position_bac_bleu():
    pass
