import { useState } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { videoDownloader } from '@/services/videoDownloader';
import { Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Header } from "./Header";
import { AppleShortcut } from "./AppleShortcut";

interface VideoInfo {
  title: string;
  thumbnail: string;
  duration: string;
  platform: string;
}

export const VideoDownloader = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const { toast } = useToast();
  const { t } = useTranslation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) {
      toast({
        title: t('error'),
        description: t('invalidUrl'),
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const info = await videoDownloader.getVideoInfo(url);
      setVideoInfo(info);
    } catch (error) {
      toast({
        title: t('error'),
        description: t('unableToFetch'),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setLoading(true);
    try {
      await videoDownloader.downloadVideo(url);
      toast({
        description: t('downloadStarted'),
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: t('error'),
        description: t('unableToDownload'),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[100dvh] flex flex-col">
      <Header />
      
      <div className="flex-1 flex flex-col items-center justify-center p-4 animate-fade-in">
        <div className="w-full max-w-xl space-y-6 px-4 sm:px-0">
          <div className="text-center space-y-3">
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
              {t('videoDownloader')}
            </h1>
            <p className="text-muted-foreground">
              {t('madeWithLove')}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                type="url"
                placeholder={t('pasteUrl')}
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="h-12 px-4 border-2 transition-all duration-200 focus:ring-2 focus:ring-black"
              />
              <Button
                type="submit"
                disabled={loading}
                className="h-12 px-6 bg-black text-white hover:bg-gray-800 transition-colors duration-200 whitespace-nowrap"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : t('check')}
              </Button>
            </div>
          </form>

          {videoInfo && (
            <div className="bg-secondary p-4 sm:p-6 rounded-lg space-y-4 animate-fade-in">
              <div className="aspect-video relative overflow-hidden rounded-lg">
                <img
                  src={videoInfo.thumbnail}
                  alt={videoInfo.title}
                  className="object-cover w-full h-full"
                />
              </div>
              <div className="space-y-2">
                <h2 className="text-lg sm:text-xl font-semibold line-clamp-2">{videoInfo.title}</h2>
                <div className="flex flex-col sm:flex-row sm:justify-between text-sm text-muted-foreground gap-1">
                  <span>{t('duration')}: {videoInfo.duration}</span>
                  <span>{t('platform')}: {videoInfo.platform}</span>
                </div>
              </div>
              <Button
                onClick={handleDownload}
                disabled={loading}
                className="w-full h-12 bg-black text-white hover:bg-gray-800 transition-colors duration-200"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  t('download')
                )}
              </Button>
            </div>
          )}
          
          <div className="mt-8">
            <AppleShortcut />
          </div>
        </div>
      </div>
    </div>
  );
};