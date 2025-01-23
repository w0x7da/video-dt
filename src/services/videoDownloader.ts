const API_URL = "http://localhost:5000";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
  author?: string;
  views?: number;
  description?: string;
  publish_date?: string;
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
      
      const response = await fetch(`${API_URL}/video_info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
      });

      console.log('API Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response data:', data);

      return {
        title: data.title || 'Untitled Video',
        thumbnail: `https://img.youtube.com/vi/${getVideoId(url)}/maxresdefault.jpg`,
        duration: formatDuration(data.length),
        platform: 'youtube',
        author: data.author,
        views: data.views,
        description: data.description,
        publish_date: data.publish_date
      };
    } catch (error) {
      console.error('Error fetching video info:', error);
      throw error;
    }
  },

  async downloadVideo(url: string): Promise<void> {
    try {
      console.log('Starting video download for URL:', url);
      
      const response = await fetch(`${API_URL}/download/720p`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
      });

      console.log('Download API Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Download API Error:', errorData);
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Download Response data:', data);

      if (data.error) {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error('Error downloading video:', error);
      throw error;
    }
  }
};

function getVideoId(url: string): string {
  const match = url.match(/[?&]v=([^&]+)/);
  return match ? match[1] : '';
}

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}