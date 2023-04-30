import requests
import json
import pandas as pd

def get_spotify_popularity(
    query_spotify: str = "items(track(name, popularity, href,album(name), artists(name)))",
    path_config: str="config.json",
    path_mapping: str='mapping_artists.json',
    path_credential: str ='credential.json'
):
    #get config dictionary
    with open(path_mapping) as mapping_file:
        mapping = json.load(mapping_file)['spotify_mapping']
    
    with open(path_config) as config_file:
        playlist_id = json.load(config_file)['spotify_playlist_id']

    with open(path_credential) as cred_file:
        credential = json.load(cred_file)

    #get bear token
    BearTokenReq = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "client_id": credential['spotify_client_id'],#"cefc62abff554ec8a708ab48043c1962",
            "client_secret": credential['spotify_client_secret']#"cd48edde2c2140a38cbf46a0735e08fc"
        }
        
    )
    BearToken = json.loads(BearTokenReq.content)

    #query used
    params = {
        "playlist_id": playlist_id,
        "fields": query_spotify,
        "limit": 40,
        "offset": 0
    }
    header = {
        "Authorization": "Bearer " + BearToken['access_token'],
        
    }
    JsonResponse = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", 
        params=params, 
        headers=header
    )

    song_res = json.loads(JsonResponse.content)

    res_dict = {
        x['track']['artists'][0]['name']: 
            x['track']['popularity'] 
        for x in song_res['items']
    }

    spotify_res = pd.DataFrame(
        res_dict.items(), 
        columns=['artista', 'popularity']
    )
    spotify_res['artista'] = spotify_res['artista'].map(mapping)

    spotify_res.to_csv('spotify_result/spotify_results.csv', index=False)

if __name__ == '__main__':
    get_spotify_popularity()