import { Smartphone } from "lucide-react";
import { Button } from "./ui/button";
import { useTranslation } from "react-i18next";

export const AppleShortcut = () => {
  const { t } = useTranslation();
  
  return (
    <div className="mt-8 flex flex-col items-center gap-4">
      <a 
        href="https://www.icloud.com/shortcuts/e2f959a437544128b4942eddcbbb23be"
        target="_blank"
        rel="noopener noreferrer"
      >
        <Button 
          className="bg-black hover:bg-gray-800 text-white border-none"
        >
          {t('getOne')} iPhone <Smartphone className="ml-2" />
        </Button>
      </a>

      <a 
        href="https://www.icloud.com/shortcuts/87a987bdce2c4a729dddad698d7fff8f"
        target="_blank"
        rel="noopener noreferrer"
      >
        <Button 
          className="bg-black hover:bg-gray-800 text-white border-none"
        >
          {t('getOne')} Youtube DT sur iPhone <Smartphone className="ml-2" />
        </Button>
      </a>
    </div>
  );
};