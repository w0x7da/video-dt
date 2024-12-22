import { useState } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { videoDownloader } from '@/services/videoDownloader';
import { Loader2 } from "lucide-react";

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) {
      toast({
        title: "Erreur",
        description: "Veuillez entrer une URL valide",
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
        title: "Erreur",
        description: "Impossible de récupérer les informations de la vidéo",
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
        title: "Succès",
        description: "Téléchargement démarré",
      });
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de télécharger la vidéo",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 animate-fade-in">
      <div className="w-full max-w-xl space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">
            Téléchargeur de Vidéos
          </h1>
          <p className="text-muted-foreground">
            Téléchargez des vidéos TikTok et instagram
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="url"
              placeholder="Collez l'URL de la vidéo ici"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="h-12 px-4 border-2 transition-all duration-200 focus:ring-2 focus:ring-black"
            />
            <Button
              type="submit"
              disabled={loading}
              className="h-12 px-6 bg-black text-white hover:bg-gray-800 transition-colors duration-200"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Vérifier"}
            </Button>
          </div>
        </form>

        {videoInfo && (
          <div className="bg-secondary p-6 rounded-lg space-y-4 animate-fade-in">
            <div className="aspect-video relative overflow-hidden rounded-lg">
              <img
                src={videoInfo.thumbnail}
                alt={videoInfo.title}
                className="object-cover w-full h-full"
              />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-semibold">{videoInfo.title}</h2>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Durée: {videoInfo.duration}</span>
                <span>Plateforme: {videoInfo.platform}</span>
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
                "Télécharger"
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};