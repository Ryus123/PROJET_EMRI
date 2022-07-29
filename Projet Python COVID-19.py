#PROD BY EMILIANO QUENUM AND EMMARIUS DELAR

#Plan:

# <---ETAPE 1: Partie du projet sans les bonus

# <---ETAPE 2: Bonus 1 et 2 proposé dans le projet

    ### Traveaux sur les dates
    ### Affichage sur Map avec le module folium

# <---ETAPE 3: Notre propre Bonus
    ## Partie 1: Dans un premier temps, l'utilisateur souhaitant se faire vacciner renseignera son adresse et la distance maximal
                # qu'il sera prêt à parcourir pour trouver un centres de vaccination qui lui convient. Ensuite le programme lui proposera
                # une liste de centres de vacinnation correspondant à ses critères
    ## Partie 2:En fonction son adresse, du centre et du moyen de transport qu'il aura choisi au préalable un lien vers l'itinéraire google maps ou un itinéraire textuel lui sera proposé.
                #(Cliquer dessus pour avoir le vissuel)



# <---ETAPE 1:
#SECTION 1 : Les imports
import os
import requests
import sys
import json
from pprint import pprint
import folium
import random
from graphh import GraphHopper



#SECTION 2 : Les fonctions

#{"types":   , ....., "features":  [ "properties": {........,    "c_structure_cp": Adresse, 'c_rdv_site_web': liens,  ....,....., etc...] }

# <---ETAPE 1:
def read_stock_json():              ####Cette fonction recupère que les liens doctolib et les stock dans une liste qu'il retourne ensuite

    list_url_doctolib= []
    url = "https://www.data.gouv.fr/fr/datasets/r/d0566522-604d-4af6-be44-a26eefa01756"  # --> Site centre-vaccination
    recup = requests.get(url)
    file_json = recup.json()
    data_center_vac = file_json["features"]                                                   # ----> liste dans lequel est situé la clé properties

    for features_details in data_center_vac:                                                # ---->Parcour de la valeur de la clé "features" qui est un liste de dico
        cp_vaccin_center = features_details["properties"]["c_structure_cp"]                   # ----> Recupère le code postale depuis la valeur de la clé "c_structure_cp" contenu dans la valeur  de la clé "properties" qui est de type dico
        url_doctolib_center = features_details["properties"]["c_rdv_site_web"]              # ----> Recupère le liens du site doctolib associé au centre de vacination depuis la valeur de la clé "c_structure_cp" contenu dans la valeur  de la clé "properties" qui est de type dico

        if  (url_doctolib_center!= None) and (cp_vaccin_center == "35000") and url_doctolib_center[: 29] == "https://partners.doctolib.fr/":
            list_url_doctolib.append(url_doctolib_center)


    return(list_url_doctolib)


def coded_split(link_list):                           ######Cette fonction prend en paramètre la liste des liens doctolib, coupe la partie precise des liens doctolib qui nous interesse, le stock dans unez liste et la retourne

    passwd_name_list = []
    for link in link_list:
        cpt_slach = 0
        SPLIT1 = ""

        for i, letter_caract in enumerate(link):

            if letter_caract == "/":                    ##### Retrouve l'indice du dernier du "/"  dans le liens
                cpt_slach = i

        for i in range(cpt_slach + 1, len(link)):
            SPLIT1 += link[i]                           #### Additionne les chaines de caractère après l'indice de "/" jusqu'as la fin du liens
        SPLIT2 = SPLIT1.split("?")                      #### Coupe la nouvelle chaine obtenu au "?" et recuperère que la partie a l'indice 0 == Nom de code
        Nom_de_code = SPLIT2[0]
        passwd_name_list.append(Nom_de_code)

    return passwd_name_list



def loading_coded_name(list_nom_d_cd):              ###### Cette fonction prend en paramètre la liste des coupures obtenu dans la fonction coded_split et genere un nouveau lien puis lance une requête qu'il transformera ensuite en fichier json.Ceux ci seront stocker dans une liste et seront retourné

    center35000_data_list = []
    headers_https = {"User-Agent": "PROJET_EMRI"}                                ###### Creation d'un USER-AGENT

    for Nom_de_code in list_nom_d_cd:
        url = "https://partners.doctolib.fr/booking/" + Nom_de_code + ".json"
        data_receive = requests.get(url, headers= headers_https)

        if data_receive != "Reponse [404]":                                 ##### Permet de mettre de coté les reponses 404 qui ne comporte aucune information
            files_json = data_receive.json()                                ##### Transformation des requete en fichier json
            center35000_data_list.append(files_json)


    return(center35000_data_list)



def visit_motives(file_json_request_list):                  ####Cette fonction prend en paramètre la liste des fichier json retourné par la fonction loading_coded_split et retourne un dictionnaire dont les clé sont les noms des centre et les valeur les liste visites motive dans lequel sont présent les premieres dose de vaccin disponible

    visit_motives_details = []
    vaccin_center = ""
    center_name_motive = {}

    for dico in file_json_request_list:

        if dico != {'status': 404, 'error': 'Not Found'}:               #####  Evite le keyError en cas de d'abscence de la clé data
            visit_motives_details = dico["data"]["visit_motives"]          ##### Récuperation de la valeur associé à la clé" visit_motives" ------> type= liste

            for vm_element_list in visit_motives_details:

                if vm_element_list["first_shot_motive"] == True:            ###### Vérifie si la valeur associé à la clé "first_shot_motive" est "True"
                    vaccin_center = dico["data"]["profile"]["name_with_title"]       ###### Récupération du nom des centre
                    center_name_motive[vaccin_center] = vm_element_list             ###### Récupération des visites motives associé aux première injections

    return (center_name_motive)

#<---ETAPE 2:   Partie bonus:

def base_de_donnee(file_json_request_list, center_name_motive):             #### "CONSTITUTION D'UNE BASE DE DONNEE POUR DES DONNEE REUTILISABLE DANS LES BONUS"
    data_det = {}
    base_donnée = {}
    passage = []

    for dico in file_json_request_list:
        for ele in dico.keys():
            if ele == "data":
                data_det = dico[ele]

        for name in center_name_motive.keys():

            if data_det["profile"]["name_with_title"] == name:               #------> vérifie si on est dans le dico[data] du centre en question
                for ele2 in data_det.keys():
                    if ele2 == "places":                                     #---> on récupère les données dans dico[data][places] associé au centre en question
                        liste_places = data_det[ele2]
                        adresse, num, lat_long, horaire = [], [], [], []
                        for i in range(len(liste_places)):
                            try:                                            #----> Certains centre n'ont pas renseigné leur numero de telephone, on essaie de recuperer l'information et si elle n'est pas présente on lui acquiert un (nouvel attribut)*
                                adresse.append(liste_places[i]['full_address']) #---> données regroupé sous forme de liste pour ne pas qu'elles soit écrasé par les suivante
                                num.append(liste_places[i]['landline_number'])
                                passage.append(liste_places[i]['latitude'])
                                passage.append(liste_places[i]['longitude'])
                                lat_long.append(passage)
                                passage = []
                                horaire.append(liste_places[i]['opening_hours'])
                                base_donnée[name] = {"adresse": adresse, "numero": num, "GPS": lat_long, "agenda": horaire} #On a trié puis stocké les données qui nous intéresse pour chaque centre dans un dictionnaire
                            except KeyError:
                                num = "Non renseigné ! "                       #---> (nouvel attribut donné)*
                                base_donnée[name] = {"adresse": adresse, "numero": num, "GPS": lat_long, "agenda": horaire}


    return base_donnée




def Horaire(base_de_donnee, n_centre='Nul'): #---> Cette fonction retourne les horaire de chaque centre de vaccination ou d'un centre précis
    j_semaine = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]  #----> jour numéroter de 0 à 6 dans la base de donnée
                                                                                        #on utilise les numéros comme indince de la liste pour #
    if n_centre == 'Nul':                                                                               #les convertir en jour de la semaine
        for name in base_de_donnee.keys():
            horaire = base_de_donnee[name]["agenda"][0]
            print("\n", "======== Le centre : {} ========".format(name), "\n")
            for i in range(len(horaire)):
                jour, heure_ouv, heure_ferm = horaire[i]["day"], horaire[i]["ranges"][0][0], horaire[i]["ranges"][0][1] #récupère les heure d'ouverture et de fermeture dans une sous-liste de liste dans la base de donnée
                days = j_semaine[jour]
                print("         est ouvert le {} de {} à {} !".format(days, heure_ouv, heure_ferm))
    else:
        horaire = base_de_donnee[n_centre]["agenda"][0]
        print("\n", "======== Le centre : {} ========".format(n_centre), "\n")
        for i in range(len(horaire)):
            jour, heure_ouv, heure_ferm = horaire[i]["day"], horaire[i]["ranges"][0][0], horaire[i]["ranges"][0][1]  # récupère les heure d'ouverture et de fermeture dans une sous-liste de liste dans la base de donnée
            days = j_semaine[jour]
            print("         est ouvert le {} de {} à {} !".format(days, heure_ouv, heure_ferm))



def Map_outpout(base_donnee): ####Affiche les centres de vacination avec des maqueurs coloré sur la carte (Avec le module folium)

    location = folium.Map()
    color = ['purple', 'darkred', 'gray', 'green', 'red', 'darkpurple', 'pink', 'cadetblue', 'lightgreen', 'blue', 'beige', 'black', 'darkblue', 'lightred', 'orange', 'darkgreen', 'lightblue', 'lightgray']

    for center_name in base_donnee.keys():

        long_lat = base_donnee[center_name]["GPS"]                   ### Retrouve les données liéés a la localisation des centres de vaccination [long, lat]
        adresse = base_donnee[center_name]["adresse"][0]
        numero = base_donnee[center_name]["numero"][0]
        color_indice = random.randint(0, (len(color))-1)             ####Pour générer des couleurs randoms

        for geo in long_lat:

            folium.Marker(location=geo, tooltip=center_name, popup= "Adresse: {}\n Télépnone: {}".format(adresse, numero), zoom_start=12, icon=folium.Icon(color=color[color_indice])).add_to(location,)   #Ajoute des marqueurs a chaque point de localisation
            location.save("index.html") #Sauvegarde le dernier etat de la carte(les modification faites)

        ### Il faut aller dans le fichier index.html pour visualiser la map folium dans votre navigateur ou dans Pycharm avec le module leaflet installer au préalable




def metro_plus_proche_centre(base_donnee, centre_voulu, gps_adresse_voulu, client): #---> Cette fonction retourne le nom de la station de metro la plus proche du centre de vaccination
    dist_max = 99999999999
    if centre_voulu != "Nul":
        gps_lieu_voulu = client.address_to_latlong(base_donnee[centre_voulu]["adresse"])
    else:
        gps_lieu_voulu = gps_adresse_voulu
    gps_metro = {"Kennedy": (48.121257, -1.713264), "Villejean-Université": (48.121263, -1.704044),
                 "Pontchaillou": (48.120901, -1.694545), "Anatole": (48.118070, -1.687643),
                 "Sainte-Anne": (48.114498, -1.680490), "République": (48.109695, -1.679261),
                 "Charles de Gaulle": (48.106485, -1.676789), "Gares" : (48.103842, -1.671933),
                 "Jacques Cartier" : (48.097531, -1.675333), "Clemenceau": (48.094157, -1.680446), "Henri Fréville" : (48.087648, -1.674745),
                 "Italie": (48.086573, -1.667848) , "Triangle": (48.086386, -1.660414), "Le Blosne" : (48.087689, -1.654271) ,
                 "La Poterie": (48.087513, -1.644571)}

    for cle, val in gps_metro.items():
        gps = [gps_lieu_voulu]
        gps.append(val)
        dist = client.distance(gps, unit="km")
        if dist_max > dist:
            dist_max = dist
            nom_arret_plus_proche = cle

    return nom_arret_plus_proche


def dist_et_temps_trajet(base_donnee, adresse_depart, nom_centre, distance_max,moyen_transport, client):  #----> Cette fonction retourne sous forme de dictionnaire le temps de trajet en fonction du moyen de transport et la distance entre un centre et la position de l'utilisateur
    gps_depart = client.address_to_latlong(adresse_depart)
    dico_dist_temps = {}
    if nom_centre == "Nul":
        for cle, val in base_donnee.items():
            center_gps = client.address_to_latlong(val["adresse"][0])
            l_lat_lont = [gps_depart]
            l_lat_lont.append(center_gps)
            dist = client.distance(l_lat_lont, unit="km")
            temps_trajet = client.duration(l_lat_lont, vehicle=moyen_transport, unit="min")
            if dist < distance_max:
                dico_dist_temps[cle] = { "distance": round(dist, 1), "temps de trajet": round(temps_trajet)}

    else:
        adresse_centre = base_donnee[nom_centre]["adresse"][0]
        for cle, val in base_donnee.items():
            center_gps = client.address_to_latlong(adresse_centre)
            l_lat_lont = [gps_depart]
            l_lat_lont.append(center_gps)
            dist = client.distance(l_lat_lont, unit="km")
            temps_trajet = client.duration(l_lat_lont, vehicle=moyen_transport, unit="min")
            if dist < distance_max:
                dico_dist_temps[cle] = {"distance": round(dist, 1), "temps de trajet": round(temps_trajet)}

    if len(dico_dist_temps.keys()) > 0:
        return dico_dist_temps
    else:
        print("Relancez le programme en utilisant une distance max plus grande ! ")
        sys.exit()



def choix_centre(base_donnee, adresse_depart, distance_max, moyen_transport, client): #Cette fonction propose a l'utilisateur l'ensemble des centres disponibles dans le perimetre choisi et retourne le nom du centre qu'il a choisi
    dico_centre_proche = dist_et_temps_trajet(base_donnee, adresse_depart, "Nul", distance_max, str(moyen_transport), client)
    compteur = 0
    dico_indice = {}
    print("\n", "Dans quel centre souhaitez-vous vous rendre ? ", "\n")
    for cle2, val in dico_centre_proche.items():
        compteur += 1
        print("     Centre numéro {} : Pour aller de {} à {} il y a une distance de {}km.".format(compteur, adresse_depart, cle2, dico_centre_proche[cle2]["distance"]))
        dico_indice[cle2] = compteur #Associe un numero (pour le choix du centre) à chaque centre afin de pouvoir retrouver le centre choisi par l'utilisateur
    print("\n", "Indiquez le numéro associé au centre de votre choix : ", end="")
    n_centre = int(input())
    for keys, val in dico_indice.items():
        if val == n_centre:
            centre_choisi = keys

    return(centre_choisi)

def choix_moyen_transport(): #Cette fonction propose a l'utilisateur les moyens de transport disponible et retourne son choix
    l_moyen_transport = ["car", "foot", "metro"]
    print("\n", " Quel moyen de transport souhaitez-vous utiliser ? ", "\n")
    compteur = 0
    for i in range(len(l_moyen_transport)):
        compteur += 1
        print(" Choix {} : si le moyen de transport est {} ! ".format(i, l_moyen_transport[i]))
    print("\n", "   Indiquez le numéro associé à votre choix : ", end="")

    choix = int(input())   #Cas erreur saisie-----------------------------------------------------------------------------------\
    while choix > compteur: #----> On s'assure que l'utilisateur réalise une bonne saisie
        print("Réessayez avec une valeur correcte : ", end="")
        choix = int(input())


    moyen_transport = l_moyen_transport[choix]
    return moyen_transport



def itinéraire(base_donnee, client): #Cette fonction retourne sous forme de dictionnaire les oonnées composants l'itinéraire pour se rendre au centre choisi
    dico_donnee = {}
    moyen_transport = choix_moyen_transport()
    print("Entrez votre adresse : ", end="")
    adresse_depart = str(input())
    print("Entrez la distance maximum que vous souhaitez parcourir (en km) : ", end="")
    distance_max = int(input())
    print("")
    gps_depart = client.address_to_latlong(adresse_depart)
    nom_centre = choix_centre(base_donnee, adresse_depart, distance_max, moyen_transport, client)
    gps_centre = base_donnee[nom_centre]['GPS'][0]
    dico_temps_dist = dist_et_temps_trajet(base_donnee, adresse_depart,nom_centre, distance_max, moyen_transport, client)
    if moyen_transport != "metro":
        dist, temps = dico_temps_dist[nom_centre]["distance"], dico_temps_dist[nom_centre]["temps de trajet"]

        dico_donnee[moyen_transport] = [dist, temps, moyen_transport, gps_depart, gps_centre]

        return(dico_donnee)

    else:
        arret_proche_du_centre = metro_plus_proche_centre(base_donnee, nom_centre, "Nul", client)
        arret_proche_adresse_depart = metro_plus_proche_centre(base_donnee, "Nul", gps_depart, client )
        dico_donnee[moyen_transport] = [adresse_depart, arret_proche_adresse_depart, arret_proche_du_centre, nom_centre]
        return dico_donnee

def loading_geo(base_donnee, dict_info, gh_client):       #######Récupération des infos liéé au points de localisations et au moyens de transports au bon format pour l'affichage sur la map

    for key in dict_info.keys():
        if key != "metro":
            moyen_transport, gps_depart, gps_center = dict_info[key][2], dict_info[key][3],dict_info[key][4]
            if moyen_transport == "car":
                moyen_transport = "driving"
            elif moyen_transport == "foot":
                moyen_transport = "walking"
            return gps_depart, gps_center, moyen_transport

        else: #---> Dans le cas ou l'utilisateur choisi "metro" comme moyen de transport : Renvoie un itinéraire textuel et les horaire associé au centre
            adresse_depart, arret_proche_adresse_depart, arret_proche_du_centre, nom_centre = dict_info["metro"][0], dict_info["metro"][1], dict_info["metro"][2], dict_info["metro"][3]
            print("\n", "=> Votre itinéraire : ")
            print("\n", "Pour aller de {} à {} en vous y rendant en métro vous devrez d'abord prendre le métro à la station {} puis descendre à la station {} ! ".format(adresse_depart, nom_centre, arret_proche_adresse_depart, arret_proche_du_centre ))
            Horaire(base_donnee, nom_centre)
            sys.exit() #--> Le programme s'arrete après avoir affiché l'itinéraire




def Map_out_parcour(donnee_trajet):          #######Permet d'afficher le trajet partant de l'adresse de départ au centre de vaccination dans google map

    gps_depart, gps_center, moyen_transport = donnee_trajet[0], donnee_trajet[1], donnee_trajet[2]
    lat1 = gps_depart[0]
    long1 = gps_depart[1]
                                            ###Recupere les info de latitude et de longitude de l'adresse de l'utilisateur et du centre de vaccination choisis
    lat2 = gps_center[0]
    long2 = gps_center[1]
    url = "https://www.google.com/maps/dir/?api=1&origin="+str(lat1)+"%2C"+str(long1)+"&destination=" +str(lat2)+"%2C"+str(long2)+"&travelmode="+moyen_transport   ####Formation du lien Google maps
    print("Cliquez sur le lien afin d'afficher votre itinéraire : ", end="")

    return url



#SECTION 3: Les tests

contenue = os.path.join("data", "credentials.json")
fp = open(contenue, "r", encoding="utf-8")
dico_api = json.load(fp)
cle_api = dico_api['GraphHopper']
gh_client = GraphHopper(api_key=cle_api)

#-----Etape 1-----
link_list = read_stock_json()


#print(read_stock_json())

#print(coded_split(link_list))


list_coded_name = coded_split (link_list)
#pprint(loading_coded_name(list_coded_name))

center_dlb_list = loading_coded_name(list_coded_name)

dico_nom_centre = visit_motives(center_dlb_list)

#pprint(dico_nom_centre)

#-----Etape 2-----

base_donnee = base_de_donnee(center_dlb_list, dico_nom_centre)

#pprint(base_donnee)

#-----Bonus 1-----

#Horaire(base_donnee)

#-----Bonus 2-----

#Map_outpout(base_donnee)

#-----Bonus 3-----

#pprint(dist_et_temps_trajet(base_donnee, "Place de la République, Rennes, France",5,"foot", gh_client))

#print(metro_plus_proche_centre(base_donnee, "Centre de vaccination COVID-19 du centre commercial ALMA", gh_client))

#choix_centre(base_donnee, "Place de la République, Rennes, France", 5, "foot", gh_client)

itinéraire(base_donnee, gh_client)

#
# dict_info = itinéraire(base_donnee, gh_client)
#
# srt_end_transport = loading_geo(base_donnee, dict_info, gh_client)
#
# #print(loading_geo(base_donnee , dict_info,gh_client))
#
# print(Map_out_parcour(srt_end_transport))

"Place de la République, Rennes, France"                            #--->Adresse utilisé pour effectuer les tests
"Place Sainte-Anne, Rennes, France"                                 #--->Adresse utilisé pour effectuer les tests
"236 BIS Rue de Nantes, Saint-Jacques-de-la-Lande, 35136, France"   #--->Adresse utilisé pour effectuer les tests