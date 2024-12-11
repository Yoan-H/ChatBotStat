# chatbotv15.py : version 15 du chatbot

import tkinter as tk
from tkinter import scrolledtext
from thefuzz import fuzz
import openai

def charger_cle_api(chemin="key.txt"):
    """
    Charge la clé API OpenAI depuis un fichier texte et la configure dans l'application.

    Args:
        chemin (str): Chemin du fichier contenant la clé API. Par défaut "key.txt".
    """
    with open(str(chemin), "r", encoding="utf-8") as f:
        openai.api_key = f.read().strip()


def charger_prompt(chemin_prompt="prompt.txt"):
    """
    Charge le prompt initial depuis un fichier texte.

    Args:
        chemin_prompt (str): Chemin du fichier texte contenant le prompt. Par défaut "prompt.txt".

    Returns:
        str: Le contenu du prompt chargé.
    """
    with open(chemin_prompt, "r", encoding="utf-8") as f:
        return f.read().strip()


def charger_base_connaissance(cours_id):
    """
    Charge le contenu de la base de connaissance d'un cours spécifique.

    Args:
        cours_id (str): L'identifiant du cours pour lequel charger le contenu.

    Returns:
        str: Le contenu de la base de connaissance du cours spécifié, ou une chaîne 
        vide si le fichier est introuvable.
    """
    chemin = f"./cours/cours{cours_id}.txt"
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Erreur : Le fichier {chemin} n'existe pas.")
        return ""


def initialiser_historique(role_bot):
    """
    Initialise l'historique des messages du chatbot.
    Cette fonction crée l'historique initial des messages avec le rôle du chatbot 
    et un message d'accueil de l'assistant.

    Arguments :
    - role_bot (str): Le rôle ou le prompt de description du chatbot.

    Returns :
    - list[dict]: Une liste de dictionnaires représentant les messages initiaux de l'historique.
                    Chaque dictionnaire contient un rôle ("system" ou "assistant") 
                    et le contenu du message associé.
    """
    return [
        {"role": "system", "content": role_bot},
        {"role": "assistant", "content": "D'accord, je suis prêt à répondre à vos questions."}
    ]

# Dictionnaire des cours avec mots-clés et poids
cours_themes = {
    "cours0": {"mots_cles": ["introduction", "présentation", "données", "massives", "concepts", "analyse", "objectifs", "outils"], "poids": 1},
    "cours1": {"mots_cles": ["rappel", "statistiques", "probabilités", "lois", "normal", "exponentielle", "tests", "t-test", "p-value", "hypothèses"], "poids": 2},
    "cours2": {"mots_cles": ["classification supervisée", "classification non supervisée", "k-means", "logistique", "apprentissage", "arbre de classification","hierarchique"], "poids": 3},
    "cours3": {"mots_cles": ["ACP", "analyse en composantes principales", "dimensionnalité", "variance", "réduction", "corrélation"], "poids": 4},
    "cours4": {"mots_cles": ["régression", "linéaire", "modèles linéaires", "multiple", "prédiction", "variables", "pente", "intercept"], "poids": 3},
    "cours5": {"mots_cles": ["analyse discriminante", "classification supervisée", "groupes", "modèles probabilistes", "distances", "analyse de Fisher"], "poids": 3},
    "cours6": {"mots_cles": ["arbres","décision","forêts","arbres de décision", "forêts aléatoires", "random forest", "random","forest", "bagging", "bootstrap", "Cart", "gini", "gain d'information"], "poids": 5}
}

def determiner_cours(question):
    """
    Détermine le cours le plus pertinent en fonction des mots-clés dans la question.
    Cette fonction analyse la question de l'utilisateur en la comparant aux mots-clés 
    associés à chaque cours. Elle utilise une mesure de similarité pour déterminer 
    le cours le plus pertinent.

    Arguments :
    - question (str): La question posée par l'utilisateur, sous forme de chaîne de caractères.

    Returns :
    - str: Le nom du cours pertinent correspondant à la question, basé sur le score le plus élevé.
    """
    question_mots = question.lower().split()
    scores = {cours: 0 for cours in cours_themes.keys()}

    for cours, data in cours_themes.items():
        mots_cles = data["mots_cles"]
        #print(mots_cles)
        poids = data["poids"]
        for mot_question in question_mots:
            for mot_cle in mots_cles:
                ratio = fuzz.ratio(mot_question, mot_cle.lower())
                if ratio >= 80:  # Seuil similarité
                    scores[cours] += poids
                    break

    cours_pertinent = max(scores, key=scores.get)
    print(f"Cours pertinent déterminé : {cours_pertinent} avec un score de {scores[cours_pertinent]}") # Affichage du cours pertinent dans le terminal
    return cours_pertinent

def calculer_tokens(texte):
    """
    Calcule le nombre de mots (estimé des tokens) dans un texte donné.
    
    Argument:
    - texte (str): Le texte à analyser.
    
    Returns:
    - int: Le nombre de mots dans le texte, utilisé comme approximation du nombre de tokens.
    """
    return len(texte.split())

def calculer_total_tokens(history):
    """
    Calcule le nombre total de tokens pour une liste de messages.
    
    Args:
    - history : L'historique des messages, où chaque message est un dictionnaire 
                        contenant au moins une clé 'content' avec le texte du message.
    
    Returns:
        int: Le nombre total de tokens dans tout l'historique des messages.
    """
    return sum(calculer_tokens(message['content']) for message in history)


def gerer_limite_historique(history, max_tokens=10000):
    """
    Gère la taille de l'historique des messages pour s'assurer qu'il ne dépasse pas une limite 
    maximale de tokens. Si la limite est dépassée, supprime les messages les plus anciens, en 
    préservant toujours le premier message.
    
    Args:
    - history : L'historique des messages à gérer.
    - max_tokens : La limite maximale de tokens autorisée pour l'historique.
    """
    while calculer_total_tokens(history) > max_tokens:
        if len(history) > 1:  # Garde le prompt initial
            history.pop(1)  # Supprime le message le plus ancien après le prompt


def chatbot(question, model="gpt-3.5-turbo"):
    """
    Génère une réponse à une question posée par l'utilisateur en interagissant avec l'API OpenAI.
    Cette fonction analyse la question pour déterminer le cours pertinent, charge la base de
    connaissance associée, et envoie la requête à l'API OpenAI.

    Arguments :
    - question (str): La question posée par l'utilisateur.
    - model (str): Le modèle d'OpenAI à utiliser pour la génération de la réponse
                    (par défaut "gpt-3.5-turbo").

    Returns :
    - str: La réponse générée par le modèle OpenAI.
    """
    try:
        # Effacer l'historique sauf le rôle de base
        global messages_history
        if not messages_history:
            messages_history = initialiser_historique(charger_prompt())
            
        # Ajouter la question
        messages_history.append({'role': 'user', 'content': question})

        # Déterminer le cours pertinent et charger la base de connaissance
        cours = determiner_cours(question)
        cours_id = cours[-1]  # Extraire l'ID du cours
        base_connaissance = charger_base_connaissance(cours_id) 
        #print("base de connaissance utilisé : " + cours_id)

        # Gérer la limite de tokens dans l'historique
        gerer_limite_historique(messages_history)
        
        # Ajouter la base de connaissance et la question
        messages_history.append({"role": "user", "content": base_connaissance})

        # Envoyer la requête à l'API OpenAI
        response = openai.chat.completions.create(
            model=model,
            messages=messages_history,
            temperature=0.7 # Température pour ajuster la créativité :
                            # plus faible = plus déterministe, plus élevée = plus imprévisible
        )

        # Récupérer la réponse
        reply_content = response.choices[0].message.content.strip()
        # Ajouter la réponse de l'assistant à l'historique
        messages_history.append({'role': 'assistant', 'content': reply_content})
        
        # Supprimer la base de connaissance de l'historique avant de retourner la réponse
        if messages_history[-2]['content'] == base_connaissance:
            messages_history.pop(-2)
        
        print(len(messages_history))
        print(messages_history)
        print(calculer_total_tokens(messages_history))
        
        return reply_content

    except Exception as e:
        return f"Erreur lors de la requête : {str(e)}"










def envoyer_message():
    """
    Envoie un message entré par l'utilisateur au chatbot et affiche la réponse dans l'interface utilisateur.
    Si l'utilisateur saisit 'quitter', la fenêtre de l'application sera fermée.
    """

    user_input = entree.get()
    if user_input.lower() == 'quitter':
        fenetre.quit()
    else:
        reponse_bot = chatbot(user_input)
        afficher_bulle(user_input, "right", "#3B7DD8", "white", "Vous")
        afficher_bulle(reponse_bot, "left", "#5A189A", "white", "Bot", scroll_to_bulle=True)
        entree.delete(0, tk.END)

def afficher_bulle(message, align, bg_color, text_color, speaker, scroll_to_bulle=False):
    """
    Affiche un message dans une bulle de dialogue dans l'interface graphique de l'application.
    Les messages peuvent être alignés à gauche ou à droite et personnalisés avec différentes couleurs de fond et de texte.

    Args:
        - message (str): Le message à afficher.
        - align (str): L'alignement du message ('left' ou 'right').
        - bg_color (str): La couleur de fond de la bulle de message.
        - text_color (str): La couleur du texte du message.
        - speaker (str): L'identité de l'émetteur du message ("Vous" ou "Bot").
        - scroll_to_bulle (bool): Si True, défile automatiquement vers le message lorsqu'il est affiché (par défaut False).
    """
    frame = tk.Frame(texte_conversation, bg=bg_color, padx=10, pady=5, bd=5, relief=tk.GROOVE)
    label = tk.Label(frame, text=f"{speaker}: {message}", bg=bg_color, fg=text_color, font=("Helvetica", 16), wraplength=300, justify="left" if align == "left" else "right")
    label.pack(side='right' if align == 'right' else 'left')
    frame.config(highlightbackground="black", highlightthickness=1)
    texte_conversation.config(state=tk.NORMAL)
    texte_conversation.window_create(tk.END, window=frame, padx=(texte_conversation.winfo_width() - 320)//2, pady=5)
    texte_conversation.insert(tk.END, "\n\n")
    texte_conversation.config(state=tk.DISABLED)
    if scroll_to_bulle:
        texte_conversation.update_idletasks()
        texte_conversation.yview_moveto(1.0)

def reset_conversation():
    """
    Réinitialise l'historique des messages de la conversation dans l'interface graphique,
    en effaçant l'affichage actuel et en redémarrant l'historique à partir du prompt initial.
    """
    global messages_history
    messages_history = initialiser_historique(charger_prompt())
    texte_conversation.config(state=tk.NORMAL)
    texte_conversation.delete(1.0, tk.END)
    texte_conversation.config(state=tk.DISABLED)

def configurer_interface(fenetre):
    """
    Configure les composants de l'interface utilisateur pour l'application chatbot,
    incluant la zone de texte, les boutons et les événements de la fenêtre.

    Args:
        - fenetre (tk.Tk): La fenêtre principale de l'application.
    """
    fenetre.title("Chatbot Statistiques")
    fenetre.config(bg="black")
    fenetre.resizable(False, True)
    global texte_conversation
    texte_conversation = scrolledtext.ScrolledText(fenetre, wrap=tk.WORD, font=("Helvetica", 16),
                                height=20, width=50, state=tk.DISABLED, bg="#1c1c1c", fg="white")
    texte_conversation.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
    texte_conversation.tag_configure("gradient", foreground="white")
    texte_conversation.insert(tk.END, "")
    global entree
    entree = tk.Entry(fenetre, width=40, font=("Helvetica", 16), bg="#333333", fg="white",
                        insertbackground="white")
    entree.pack(padx=10, pady=5, side=tk.BOTTOM, fill=tk.X)
    fenetre.bind('<Return>', lambda event: envoyer_message())
    bouton_reset = tk.Button(fenetre, text="Réinitialiser", command=reset_conversation, bg="white",
                            fg="black", font=("Helvetica", 14, "bold"), relief="ridge", bd=3)
    bouton_reset.pack(padx=10, pady=5, side=tk.TOP, anchor='w')
    bouton_envoyer = tk.Button(fenetre, text="Envoyer", command=envoyer_message, bg="white",
                            fg="black", font=("Helvetica", 14, "bold"), relief="ridge", bd=3)
    bouton_envoyer.pack(padx=10, pady=5, side=tk.BOTTOM)
    fenetre.bind("<Button-1>", commencer_deplacement)
    fenetre.bind("<B1-Motion>", deplacer_fenetre)

def commencer_deplacement(event):
    """
    Initialise la position pour le déplacement de la fenêtre de l'application.

    Args:
        - event: L'événement associé à la pression d'un bouton de la souris.
    """
    global posX, posY
    posX = event.x
    posY = event.y

def deplacer_fenetre(event):
    """
    Déplace la fenêtre de l'application en fonction du mouvement de la souris,
    calculé à partir de la position initiale enregistrée lors du premier clic.

    Args:
        - event: L'événement associé au mouvement de la souris avec un bouton enfoncé.
    """
    delta_x = event.x - posX
    delta_y = event.y - posY
    x = fenetre.winfo_x() + delta_x
    y = fenetre.winfo_y() + delta_y
    fenetre.geometry(f"+{x}+{y}")






# Définitions des variables globale 
messages_history = []
fenetre = None
texte_conversation = None
entree = None
posX = 0
posY = 0

def main():
    """
    Fonction principale pour démarrer l'application de chatbot.
    Charge la clé API, initialise l'historique des messages avec le prompt initial, et configure
    l'interface utilisateur de l'application. La boucle principale de l'interface graphique est
    exécutée à partir de cette fonction.
    """
    charger_cle_api()
    global messages_history
    messages_history = initialiser_historique(charger_prompt())
    global fenetre
    fenetre = tk.Tk()
    fenetre.geometry("600x900")
    configurer_interface(fenetre)
    fenetre.mainloop()

if __name__ == "__main__":
    main()
