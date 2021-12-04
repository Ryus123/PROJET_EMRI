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


def dist_et_temps_trajet(base_donnee, adresse_depart,distance_max,moyen_transport, client):
    gps_depart = client.address_to_latlong(adresse_depart)
    dico_dist_km = {}
    dico_temps_min = {}
    for cle, val in base_donnee.items():
        center_gps = client.address_to_latlong(val["adresse"][0])
        l_lat_lont = [gps_depart]
        l_lat_lont.append(center_gps)
        dist = client.distance(l_lat_lont, unit="km")
        temps_trajet = client.duration(l_lat_lont,vehicle=moyen_transport, unit="min")
        if dist < distance_max :
            dico_dist_km["De " + adresse_depart + " à " + cle] = round(dist, 1)
            dico_temps_min["De " + adresse_depart + " à " + cle] = round(temps_trajet)

    return dico_dist_km, dico_temps_min

#def trajet_metro(gps_metro):



gps_metro = { "Kennedy": (48.121404, -1.708946), "Villejean-Université" : (48.121265, -1.704041), "Pontchaillou" : (48.120901, -1.694545), "Anatole" : (48.119072, -1.685926), "Sainte-Anne" : (48.114620, -1.680837), "République" : (48.110027, -1.679200), "Charles de Gaulle" : (48.106485, -1.676789), "La Poterie" : (48.087495, -1.644572)}




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


#Moyen transport possible :  [“car”, “foot”, “bike”, “scooter”, "metro"]
pprint(dist_et_temps_trajet(base_donnee, "Place de la République, Rennes, France",5,"foot", gh_client))

#Horaire(base_donnee)
#Map_outpout(base_donnee)
#SECTION 3 TESTS




#[SORTIE]