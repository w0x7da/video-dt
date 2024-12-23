const RAPID_API_KEY = "9aed925b29msh2aa707be2332276p12fd68jsncf8eccea39b7";
const BASE_URL = "https://youtube-shorts-video-downloader-and-converter.p.rapidapi.com";

const MAX_RETRIES = 3;
const TIMEOUT = 30000; // 30 secondes

async function fetchWithTimeout(url: string, options: RequestInit, timeout: number) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

async function fetchWithRetry(url: string, options: RequestInit, retries: number = MAX_RETRIES) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetchWithTimeout(url, options, TIMEOUT);
      
      if (!response.ok) {
        const errorBody = await response.text();
        console.error(`Attempt ${i + 1} failed with status ${response.status}:`, errorBody);
        
        if (response.status === 504 && i < retries - 1) {
          console.log(`Retrying... Attempt ${i + 2} of ${retries}`);
          continue;
        }
        
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      console.log(`Attempt ${i + 1} failed, retrying...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // Exponential backoff
    }
  }
  throw new Error('Max retries reached');
}

export const youtubeApi = {
  async getVideoInfo(url: string) {
    try {
      console.log('Fetching video info for URL:', url);
      
      const videoId = extractYoutubeId(url);
      if (!videoId) {
        throw new Error('ID de vidéo YouTube invalide');
      }

      const response = await fetchWithRetry(`${BASE_URL}/get-video-info/${videoId}`, {
        method: 'GET',
        headers: {
          'x-rapidapi-host': 'youtube-shorts-video-downloader-and-converter.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        }
      });

      const data = await response.json();
      console.log('API Response:', data);

      if (!data || !data.title) {
        throw new Error('Réponse API invalide');
      }

      return {
        title: data.title || 'Vidéo YouTube',
        thumbnail: data.thumbnail || '',
        duration: formatDuration(data.duration) || '00:00',
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
      
      const videoId = extractYoutubeId(url);
      if (!videoId) {
        throw new Error('ID de vidéo YouTube invalide');
      }

      const response = await fetchWithRetry(`${BASE_URL}/download-short-mp4/${videoId}?quality=480p`, {
        method: 'GET',
        headers: {
          'x-rapidapi-host': 'youtube-shorts-video-downloader-and-converter.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        }
      });

      const data = await response.json();
      console.log('Download API Response:', data);

      if (!data || !data.url) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      return data.url;
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