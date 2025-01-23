const YT_DLP_API = "https://dlpanda.com/api/v2/video";
const API_KEY = "dp_Z5qYWE9876XyPkL2mN4Jt";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

interface ApiResponse {
  status: string;
  title?: string;
  thumbnail?: string;
  duration?: number;
  url?: string;
  error?: string;
  videoUrl?: string;
}

export const videoDownloader = {
  async getVideoInfo(url: string): Promise<VideoInfo> {
    try {
      console.log('Fetching video info for URL:', url);
      
      const response = await fetch(`${YT_DLP_API}/info?key=${API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          url: url
        })
      });

      console.log('API Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      console.log('API Response data:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      const platform = detectPlatform(url);
      let duration = '00:00';
      
      if (data.duration) {
        const minutes = Math.floor(data.duration / 60);
        const seconds = data.duration % 60;
        duration = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      }

      return {
        title: data.title || 'Vidéo sans titre',
        thumbnail: data.thumbnail || '',
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
      console.log('Starting video download for URL:', url);
      
      const response = await fetch(`${YT_DLP_API}/download?key=${API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          url: url,
          format: 'mp4'
        })
      });

      console.log('Download API Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Download API Error:', errorData);
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      console.log('Download Response data:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      if (!data.videoUrl) {
        throw new Error('Aucun lien de téléchargement disponible');
      }

      const videoResponse = await fetch(data.videoUrl);
      const blob = await videoResponse.blob();
      
      const downloadElement = document.createElement('a');
      downloadElement.href = URL.createObjectURL(blob);
      
      const platform = detectPlatform(url);
      downloadElement.download = `${platform}_${Date.now()}.mp4`;
      
      document.body.appendChild(downloadElement);
      downloadElement.click();
      document.body.removeChild(downloadElement);
      
      URL.revokeObjectURL(downloadElement.href);
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};

function detectPlatform(url: string): string {
  if (url.includes('instagram.com')) return 'instagram';
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'youtube';
  if (url.includes('tiktok.com')) return 'tiktok';
  if (url.includes('twitter.com') || url.includes('x.com')) return 'twitter';
  if (url.includes('facebook.com') || url.includes('fb.watch')) return 'facebook';
  return 'unknown';
}