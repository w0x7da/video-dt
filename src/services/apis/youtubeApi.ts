const RAPID_API_KEY = "9aed925b29msh2aa707be2332276p12fd68jsncf8eccea39b7";
const BASE_URL = "https://ytstream-download-youtube-videos.p.rapidapi.com/dl";

export const youtubeApi = {
  async getVideoInfo(url: string) {
    try {
      console.log('Fetching video info for URL:', url);
      
      // Extraire l'ID de la vidéo de l'URL YouTube
      const videoId = extractYoutubeId(url);
      if (!videoId) {
        throw new Error('ID de vidéo YouTube invalide');
      }

      const response = await fetch(`${BASE_URL}?id=${videoId}`, {
        method: 'GET',
        headers: {
          'x-rapidapi-host': 'ytstream-download-youtube-videos.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        }
      });

      if (!response.ok) {
        console.error('API Response not OK:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response data:', data);

      return {
        title: data?.title || 'Vidéo YouTube',
        thumbnail: data?.thumb?.url || '',
        duration: formatDuration(data?.length) || '00:00',
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
      
      // Extraire l'ID de la vidéo de l'URL YouTube
      const videoId = extractYoutubeId(url);
      if (!videoId) {
        throw new Error('ID de vidéo YouTube invalide');
      }

      const response = await fetch(`${BASE_URL}?id=${videoId}`, {
        method: 'GET',
        headers: {
          'x-rapidapi-host': 'ytstream-download-youtube-videos.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        }
      });

      if (!response.ok) {
        console.error('Download API Response not OK:', response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Download API Response data:', data);

      // Récupérer le lien de la meilleure qualité disponible
      const downloadUrl = data?.formats?.[0]?.url;
      
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

// Fonction utilitaire pour extraire l'ID d'une vidéo YouTube d'une URL
function extractYoutubeId(url: string): string | null {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
}

// Fonction utilitaire pour formater la durée
function formatDuration(seconds: number): string {
  if (!seconds) return '00:00';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}