const RAPID_API_KEY = "9aed925b29msh2aa707be2332276p12fd68jsncf8eccea39b7";
const BASE_URL = "https://youtube-media-downloader.p.rapidapi.com/v2/misc/list-items";

export const youtubeApi = {
  async getVideoInfo(url: string) {
    try {
      console.log('Fetching video info for URL:', url);
      
      const response = await fetch(BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'x-rapidapi-host': 'youtube-media-downloader.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        },
        body: new URLSearchParams({
          url: url
        })
      });

      if (!response.ok) {
        console.error('API Response not OK:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response data:', data);

      // Extraction des informations pertinentes de la réponse
      const videoData = data.items[0];
      return {
        title: videoData?.title || 'Vidéo YouTube',
        thumbnail: videoData?.thumbnail?.url || '',
        duration: videoData?.duration || '00:00',
        platform: 'YouTube'
      };
    } catch (error) {
      console.error('Error in getVideoInfo:', error);
      throw error;
    }
  },

  async downloadVideo(url: string) {
    try {
      console.log('Downloading video for URL:', url);
      
      const response = await fetch(BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'x-rapidapi-host': 'youtube-media-downloader.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        },
        body: new URLSearchParams({
          url: url
        })
      });

      if (!response.ok) {
        console.error('Download API Response not OK:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Download API Response data:', data);

      // Récupération du lien de téléchargement de la meilleure qualité disponible
      const downloadUrl = data.items[0]?.formats?.find((f: any) => f.quality === 'high')?.url || 
                         data.items[0]?.formats?.[0]?.url;
      
      if (!downloadUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      return downloadUrl;
    } catch (error) {
      console.error('Error in downloadVideo:', error);
      throw error;
    }
  }
};