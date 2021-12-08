#PROD BY EMILIANO QUENUM  AND EMMARIUS DELAR

#SECTION 1 IMPORTS
import os
import requests
import json
from pprint import pprint
import folium
import random
from graphh import GraphHopper


#SECTION 2 FONCTIONS

#{"types":   , ....., "features":  [ "properties": {........,    "c_structure_cp": Adresse, 'c_rdv_site_web': liens,  ....,....., etc...] }

# <---ETAPE 1:
def read_stock_json():
    list_url_doctolib= []
    url = "https://www.data.gouv.fr/fr/datasets/r/d0566522-604d-4af6-be44-a26eefa01756"  # --> Site centre-vaccination
    recup= requests.get(url)
    file_json= recup.json()

    data_center_vac= file_json["features"]                                          # ----> liste dans lequel est situé la clé properties
    for features_details in data_center_vac:                                        # ---->Parcour de la valeur de la clé "features" qui est un liste de dico

        cp_vaccin_center= features_details["properties"]["c_structure_cp"]          # ----> Recupère le code postale depuis la valeur de la clé "c_structure_cp" contenu dans la valeur  de la clé "properties" qui est de type dico

        url_doctolib_center = features_details["properties"]["c_rdv_site_web"]      # ----> Recupère le liens du site doctolib associé au centre de vacination depuis la valeur de la clé "c_structure_cp" contenu dans la valeur  de la clé "properties" qui est de type dico
        if  (url_doctolib_center!= None) and (cp_vaccin_center== "35000")   and  url_doctolib_center[: 29] == "https://partners.doctolib.fr/":


            list_url_doctolib.append(url_doctolib_center)


    return(list_url_doctolib)

def loading_coded_name(link_list):

    passwd_name_list= []

    for link in link_list:
        cpt_slach = 0
        SPLIT1 = ""
        for i, letter_caract in enumerate(link):

            if letter_caract == "/":
                cpt_slach = i

        for i in range(cpt_slach + 1, len(link)):
            SPLIT1 += link[i]


        SPLIT2 = SPLIT1.split("?")

        Nom_de_code = SPLIT2[0]


        passwd_name_list.append(Nom_de_code)

    return(passwd_name_list)

#<---ETAPE 2:


def coded_split(list_nom_d_cd):
    center35000_data_list= []
    headers_https= {"User-Agent": "PROJET_EMRI"}
    for Nom_de_code in list_nom_d_cd:

        url= "https://partners.doctolib.fr/booking/" + Nom_de_code + ".json"

        data_receive= requests.get(url, headers= headers_https)
        if data_receive!= "Reponse [404]":

            files_json = data_receive.json()

            center35000_data_list.append(files_json)


    return(center35000_data_list)



def visit_motives(file_json_request_list):

    visit_motives_details = []
    vaccin_center = ""
    center_name_motive = {}
    for dico in file_json_request_list:

        if dico != {'status': 404, 'error': 'Not Found'}:

            visit_motives_details = dico["data"]["visit_motives"]

            for vm_element_list in visit_motives_details:

                if vm_element_list["first_shot_motive"] == True:

                    vaccin_center =dico["data"]["profile"]["name_with_title"]

                    center_name_motive[vaccin_center] = vm_element_list

    return (center_name_motive)

def base_de_donnee(file_json_request_list, center_name_motive):
    data_det= {}
    base_donnée = {}
    passage=[]
    for dico in file_json_request_list:
        for ele in dico.keys():
            if ele == "data":
                data_det = dico[ele]
        for name in center_name_motive.keys():

            if data_det["profile"]["name_with_title"] == name:               #------> vérifie si on est dans le dico[data] du centre en question
                for ele2 in data_det.keys():
                    if ele2 == "places":                                     #---> on récupère les données dans dico[data][places] associé au centre en question
                        liste_places = data_det[ele2]
                        adresse, num , lat_long, horaire = [], [], [], []
                        for i in range(len(liste_places)):                  #---> on récupère chaque information pour le centre souhaité dans chacun des dico[data][places] qui le concerne
                            try:                                            #----> Certains centre n'ont pas renseigné leur numero de telephone, on essaie de recuperer l'information et si elle n'est pas présente on lui acquiert un (nouvel attribut)*
                                adresse.append(liste_places[i]['full_address']) #---> données regroupé sous forme de liste pour ne pas qu'elles soit écrasé par les précédentes
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

def Horaire(base_de_donnee): #---> on travail sur la base de donnée trié et stocké pour simplifier le code
    j_semaine = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]  #----> jour numéroter de 0 à 6 dans la base de donnée
                                                                                        #on utilise les numéros comme indince de la liste pour #
                                                                                        #les convertir en jour de la semaine
    for name in base_de_donnee.keys():
        horaire = base_de_donnee[name]["agenda"][0]
        print("\n","======== Le centre : {} ========".format(name), "\n")
        for i in range(len(horaire)):
            jour, heure_ouv, heure_ferm = horaire[i]["day"], horaire[i]["ranges"][0][0], horaire[i]["ranges"][0][1] #récupère les heure d'ouverture et de fermeture dans une sous-liste de liste dans la base de donnée
            days = j_semaine[jour]
            print("Est ouvert le {} de {} à {} !".format(days, heure_ouv, heure_ferm))


def Map_outpout(base_donnee):

    location = folium.Map()
    color= ['purple', 'darkred', 'gray', 'green', 'red', 'darkpurple', 'pink', 'cadetblue', 'lightgreen', 'blue', 'beige', 'black', 'darkblue', 'lightred', 'orange', 'darkgreen', 'lightblue', 'lightgray']
    for center_name in base_donnee.keys():

        long_lat= base_donnee[center_name]["GPS"] ### Retrouve les données liéés a la localisation des centres de vaccination [long, lat]
        adresse= base_donnee[center_name]["adresse"][0]
        numero=base_donnee[center_name]["numero"][0]
        color_indice= random.randint(0, (len(color))-1)



        for geo in long_lat:

            folium.Marker(location=geo, tooltip=center_name, popup= "Adresse: {}\n Télépnone: {}".format(adresse,numero), zoom_start=12, icon=folium.Icon(color=color[color_indice])).add_to(location,)   #Ajoute des marqueurs a chaque point de localisation
            location.save("index.html") #Sauvegarde le dernier etat de la carte(les modification faites)


contenue = os.path.join("data", "credentials.json")
fp = open(contenue, "r", encoding="utf-8")
dico_api = json.load(fp)
cle_api = dico_api['GraphHopper']
gh_client = GraphHopper(api_key= cle_api)


def metro_plus_proche_centre(base_donnee, centre_voulu, gps_adresse_voulu, client):
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


def dist_et_temps_trajet(base_donnee, adresse_depart, nom_centre, distance_max,moyen_transport, client):
    gps_depart = client.address_to_latlong(adresse_depart)
    dico_dist_temps = {}
    if nom_centre == "Nul":
        for cle, val in base_donnee.items():
            center_gps = client.address_to_latlong(val["adresse"][0])
            l_lat_lont = [gps_depart]
            l_lat_lont.append(center_gps)
            dist = client.distance(l_lat_lont, unit="km")
            temps_trajet = client.duration(l_lat_lont,vehicle=moyen_transport, unit="min")
            if dist < distance_max :
                dico_dist_temps[cle] = { "distance" : round(dist, 1), "temps de trajet" : round(temps_trajet)}

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

    return dico_dist_temps

def choix_centre(base_donnee, adresse_depart, distance_max, moyen_transport, client):
    dico_centre_proche = dist_et_temps_trajet(base_donnee, adresse_depart, "Nul", distance_max, moyen_transport, client)
    compteur = 0
    dico_indice = {}
    print("\n", "Dans quel centre souhaitez-vous vous rendre ? ", "\n")
    for cle2, val in dico_centre_proche.items():
        compteur += 1
        print("     Centre numéro {} : Pour aller de {} à {} il y a une distance de {}km.".format(compteur, adresse_depart, cle2, dico_centre_proche[cle2]["distance"]))
        dico_indice[cle2] = compteur
    print("\n","Indiquez le numéro associé au centre de votre choix : ", end="")
    n_centre = int(input())
    for keys, val in dico_indice.items():
        if val == n_centre :
            centre_choisi = keys

    return(centre_choisi)

def choix_moyen_transport():
    l_moyen_transport = ["car", "foot", "bike", "scooter", "metro"]
    print("\n", " Quel moyen de transport souhaitez-vous utiliser ? ", "\n")
    for i in range(len(l_moyen_transport)):
        print(" Choix {} : si le moyen de transport est {} ! ".format(i, l_moyen_transport[i]))
    print("\n", "   Indiquez le numéro associé à votre choix : ", end="")
    choix = int(input())
    moyen_transport = l_moyen_transport[choix]
    return moyen_transport



def itinéraire(base_donnee, client):
    moyen_transport = choix_moyen_transport()
    print("Entrez votre adresse : ", end="")
    adresse_depart = str(input())
    print("Entrez la distance maximum que vous souhaitez parcourir (en km) : ", end="")
    distance_max = int(input())
    print("")
    liste_arret_metro = ["Kennedy", "Villejean-Université","Pontchaillou", "Anatole","Sainte-Anne", "République","Charles de Gaulle", "Gares" ,"Jacques Cartier" , "Clemenceau", "Henri Fréville" ,"Italie", "Triangle", "Le Blosne","La Poterie"]
    gps_depart = client.address_to_latlong(adresse_depart)
    nom_centre = choix_centre(base_donnee, adresse_depart, distance_max, moyen_transport, client)
    dico_temps_dist = dist_et_temps_trajet(base_donnee, adresse_depart,nom_centre, distance_max, moyen_transport, client)
    if moyen_transport != "metro":
        dist, temps = dico_temps_dist[nom_centre]["distance"], dico_temps_dist[nom_centre]["temps de trajet"]

        print( dist, temps, moyen_transport, nom_centre )
    else:
        arret_proche_du_centre = metro_plus_proche_centre(base_donnee, nom_centre, "Nul", client)
        arret_proche_adresse_depart = metro_plus_proche_centre(base_donnee, "Nul", gps_depart, client )
        for i in range(len(liste_arret_metro)):
            if liste_arret_metro[i] == arret_proche_adresse_depart:
                borne1 = i
            if liste_arret_metro[i] == arret_proche_du_centre:
                borne2 = i
        liste_itiniraire = []
        for n in range(borne1, borne2 + 1):
            liste_itiniraire.append(liste_arret_metro[n])

    print( adresse_depart, liste_itiniraire, nom_centre)






#Section 3:




link_list=  read_stock_json()


#print(read_stock_json())

#print(loading_coded_name(link_list))


list_coded_name= loading_coded_name(link_list)
#pprint(coded_split(list_coded_name))

center_dlb_list= coded_split(list_coded_name)

dico_nom_centre = visit_motives(center_dlb_list)

#pprint(dico_nom_centre)

base_donnee = base_de_donnee(center_dlb_list, dico_nom_centre)
#pprint(base_donnee)

#Horaire(base_donnee)
#Map_outpout(base_donnee)

#Moyen transport possible :  [“car”, “foot”, “bike”, “scooter”, "metro"]
#pprint(dist_et_temps_trajet(base_donnee, "Place de la République, Rennes, France",5,"foot", gh_client))

#print(metro_plus_proche_centre(base_donnee, "Centre de vaccination COVID-19 du centre commercial ALMA", gh_client))
#choix_centre(base_donnee, "Place de la République, Rennes, France",5,"foot", gh_client)

itinéraire(base_donnee, gh_client)
"Place de la République, Rennes, France"  #--->Adresse utilisé pour effectuer les tests
"Place Sainte-Anne, Rennes, France"       #--->Adresse utilisé pour effectuer les tests
"236 BIS Rue de Nantes, Saint-Jacques-de-la-Lande, 35136, France"  #--->Adresse utilisé pour effectuer les tests


#SECTION 3 TESTS




#[SORTIE]
