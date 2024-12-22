export const createDownloadLink = (blob: Blob, platform: string): string => {
  const downloadElement = document.createElement('a');
  const url = URL.createObjectURL(blob);
  downloadElement.href = url;
  downloadElement.download = `${platform.toLowerCase()}_${Date.now()}.mp4`;
  return url;
};

export const findBestQualityUrl = (data: any): string => {
  let downloadUrl = '';
  
  if (data.medias && Array.isArray(data.medias)) {
    const qualities = ['hd_no_watermark', 'no_watermark', 'hd', 'high', 'sd'];
    
    for (const quality of qualities) {
      const media = data.medias.find((m: any) => 
        (m.quality === quality || m.quality?.toLowerCase().includes(quality)) && 
        m.type === 'video'
      );
      if (media) {
        downloadUrl = media.url;
        break;
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

  return downloadUrl;
};