const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const BASE_URL_INSTAGRAM = "https://zylalabs.com/api/2883/instagram+photo+and+video+saver+api/3005";
const BASE_URL_UNIVERSAL = "https://zylalabs.com/api/5393/universal+social+downloader+api/6986";
const BASE_URL_TWITTER = "https://zylalabs.com/api/4148/twitter+video+download+api/6143";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

interface Media {
  url: string;
  quality: string;
  extension: string;
  type: string;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      let apiUrl;
      let method = 'GET';
      const headers = {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      };
      
      // Déterminer quelle API utiliser en fonction de l'URL
      if (url.includes('instagram.com')) {
        apiUrl = `${BASE_URL_INSTAGRAM}/content+downloader?url=${encodeURIComponent(url)}`;
      } else if (url.includes('twitter.com') || url.includes('x.com')) {
        apiUrl = `${BASE_URL_TWITTER}/get+video`;
        method = 'POST';
      } else {
        apiUrl = `${BASE_URL_UNIVERSAL}/download+social+media+content`;
        method = 'POST';
      }

      const response = await fetch(apiUrl, {
        method,
        headers,
        body: method === 'POST' ? JSON.stringify({ url }) : undefined
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('API Response:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      // Détecter la plateforme à partir de l'URL
      let platform = 'Inconnu';
      if (url.includes('instagram.com')) platform = 'Instagram';
      else if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'YouTube';
      else if (url.includes('tiktok.com')) platform = 'TikTok';
      else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'Twitter';
      else if (url.includes('facebook.com') || url.includes('fb.watch')) platform = 'Facebook';

      // Convertir la durée en format lisible
      let duration = data.duration || data.Duration || '00:00';
      if (typeof duration === 'number') {
        const minutes = Math.floor(duration / 60000);
        const seconds = Math.floor((duration % 60000) / 1000);
        duration = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }

      // Gérer les différents formats de réponse selon la plateforme
      const title = data.title || data.Title || data.caption || data.description || 'Vidéo sans titre';
      const thumbnail = data.thumbnail || data.Thumbnail || data.cover || data.thumbnail_url || '';

      return {
        title,
        thumbnail,
        duration,
        platform
      };
    } catch (error) {
      console.error('Error fetching video info:', error);
      throw error;
    }
  },

  async downloadVideo(url: string): Promise<void> {
    try {
      let apiUrl;
      let method = 'GET';
      const headers = {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json'
      };
      
      // Déterminer quelle API utiliser en fonction de l'URL
      if (url.includes('instagram.com')) {
        apiUrl = `${BASE_URL_INSTAGRAM}/content+downloader?url=${encodeURIComponent(url)}`;
      } else if (url.includes('twitter.com') || url.includes('x.com')) {
        apiUrl = `${BASE_URL_TWITTER}/get+video`;
        method = 'POST';
      } else {
        apiUrl = `${BASE_URL_UNIVERSAL}/download+social+media+content`;
        method = 'POST';
      }

      const response = await fetch(apiUrl, {
        method,
        headers,
        body: method === 'POST' ? JSON.stringify({ url }) : undefined
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Download Response:', data);
      
      let downloadUrl = '';
      
      // Chercher la meilleure qualité sans filigrane selon la plateforme
      if (data.medias && Array.isArray(data.medias)) {
        const qualities = ['hd_no_watermark', 'no_watermark', 'hd', 'high', 'sd', 'watermark'];
        
        for (const quality of qualities) {
          const media = data.medias.find((m: Media) => 
            (m.quality === quality || m.quality?.toLowerCase().includes(quality)) && 
            m.type === 'video'
          );
          if (media) {
            downloadUrl = media.url;
            break;
          }
        }
      }

      // Fallback sur les différents formats de réponse selon la plateforme
      if (!downloadUrl) {
        downloadUrl = data.downloadLink || 
                     data.DownloadLink || 
                     data.url || 
                     data.URL ||
                     data.hd_download_url ||
                     data.download_url ||
                     data.video_url;
      }

      if (!downloadUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      // Télécharger la vidéo
      const videoResponse = await fetch(downloadUrl);
      const blob = await videoResponse.blob();
      
      // Créer un lien de téléchargement temporaire
      const downloadElement = document.createElement('a');
      downloadElement.href = URL.createObjectURL(blob);
      
      // Générer un nom de fichier basé sur la plateforme
      const platform = url.includes('instagram.com') ? 'instagram' :
                      url.includes('youtube.com') || url.includes('youtu.be') ? 'youtube' :
                      url.includes('tiktok.com') ? 'tiktok' :
                      url.includes('twitter.com') || url.includes('x.com') ? 'twitter' :
                      url.includes('facebook.com') || url.includes('fb.watch') ? 'facebook' : 'video';
      
      downloadElement.download = `${platform}_${Date.now()}.mp4`;
      
      // Déclencher le téléchargement
      document.body.appendChild(downloadElement);
      downloadElement.click();
      document.body.removeChild(downloadElement);
      
      // Nettoyer l'URL temporaire
      URL.revokeObjectURL(downloadElement.href);
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};