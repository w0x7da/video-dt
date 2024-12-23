const API_KEY = "6079|kQr3TNBAD4pT2xWNP1TBP0pNZVbM3zzeSmEw3YtN";
const RAPID_API_KEY = "9aed925b29msh2aa707be2332276p12fd68jsncf8eccea39b7";
const BASE_URL_INSTAGRAM = "https://zylalabs.com/api/2883/instagram+photo+and+video+saver+api/3005";
const BASE_URL_UNIVERSAL = "https://zylalabs.com/api/5393/universal+social+downloader+api/6986";
const BASE_URL_TWITTER = "https://zylalabs.com/api/4148/twitter+video+download+api/6143";
const BASE_URL_YOUTUBE = "https://youtube-to-mp4.p.rapidapi.com";

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
      let headers: HeadersInit = {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      };
      let body;
      
      // Déterminer quelle API utiliser en fonction de l'URL
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        apiUrl = `${BASE_URL_YOUTUBE}/url=&title?url=${encodeURIComponent(url)}`;
        headers = {
          'x-rapidapi-host': 'youtube-to-mp4.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        };
      } else if (url.includes('instagram.com')) {
        apiUrl = `${BASE_URL_INSTAGRAM}/content+downloader?url=${encodeURIComponent(url)}`;
      } else if (url.includes('twitter.com') || url.includes('x.com')) {
        apiUrl = `${BASE_URL_TWITTER}/get+video`;
        method = 'POST';
        body = JSON.stringify({ url });
      } else {
        apiUrl = `${BASE_URL_UNIVERSAL}/download+social+media+content`;
        method = 'POST';
        body = JSON.stringify({ url });
      }

      const response = await fetch(apiUrl, {
        method,
        headers,
        body: method === 'POST' ? body : undefined
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

      // Traitement spécial pour YouTube via RapidAPI
      if (platform === 'YouTube') {
        return {
          title: data.title || 'Vidéo YouTube',
          thumbnail: data.thumbnail || '',
          duration: data.duration || '00:00',
          platform
        };
      }

      // Pour les autres plateformes, garder le traitement existant
      const duration = data.duration || data.Duration || '00:00';
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
      let headers: HeadersInit = {
        'Authorization': `Bearer ${API_KEY}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      };
      let body;
      
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        apiUrl = `${BASE_URL_YOUTUBE}/url=&title?url=${encodeURIComponent(url)}`;
        headers = {
          'x-rapidapi-host': 'youtube-to-mp4.p.rapidapi.com',
          'x-rapidapi-key': RAPID_API_KEY
        };
      } else if (url.includes('instagram.com')) {
        apiUrl = `${BASE_URL_INSTAGRAM}/content+downloader?url=${encodeURIComponent(url)}`;
      } else if (url.includes('twitter.com') || url.includes('x.com')) {
        apiUrl = `${BASE_URL_TWITTER}/get+video`;
        method = 'POST';
        body = JSON.stringify({ url });
      } else {
        apiUrl = `${BASE_URL_UNIVERSAL}/download+social+media+content`;
        method = 'POST';
        body = JSON.stringify({ url });
      }

      const response = await fetch(apiUrl, {
        method,
        headers,
        body: method === 'POST' ? body : undefined
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Download Response:', data);
      
      let downloadUrl = '';
      
      // Traitement spécial pour YouTube via RapidAPI
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        downloadUrl = data.url || '';
      } else {
        // Pour les autres plateformes, garder le traitement existant
        if (data.medias && Array.isArray(data.medias)) {
          const qualities = ['1080p', '720p', '480p', '360p', '240p', '144p'];
          for (const quality of qualities) {
            const media = data.medias.find((m: Media) => 
              m.quality === quality && m.type === 'video'
            );
            if (media) {
              downloadUrl = media.url;
              break;
            }
          }
          
          if (!downloadUrl) {
            const videoMedia = data.medias.find((m: Media) => m.type === 'video');
            if (videoMedia) {
              downloadUrl = videoMedia.url;
            }
          }
        }

        if (!downloadUrl) {
          downloadUrl = data.downloadLink || 
                       data.DownloadLink || 
                       data.url || 
                       data.URL ||
                       data.hd_download_url ||
                       data.download_url ||
                       data.video_url;
        }
      }

      if (!downloadUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      const downloadElement = document.createElement('a');
      downloadElement.href = downloadUrl;
      
      const platform = url.includes('instagram.com') ? 'instagram' :
                      url.includes('youtube.com') || url.includes('youtu.be') ? 'youtube' :
                      url.includes('tiktok.com') ? 'tiktok' :
                      url.includes('twitter.com') || url.includes('x.com') ? 'twitter' :
                      url.includes('facebook.com') || url.includes('fb.watch') ? 'facebook' : 'video';
      
      downloadElement.download = `${platform}_${Date.now()}.mp4`;
      downloadElement.target = '_blank';
      
      document.body.appendChild(downloadElement);
      downloadElement.click();
      document.body.removeChild(downloadElement);
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};