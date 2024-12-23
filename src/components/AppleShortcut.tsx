import { Smartphone } from "lucide-react";
import { Button } from "./ui/button";
import { useTranslation } from "react-i18next";

export const AppleShortcut = () => {
  const { t } = useTranslation();
  
  return (
    <div className="mt-8 flex justify-center">
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
    </div>
  );
};