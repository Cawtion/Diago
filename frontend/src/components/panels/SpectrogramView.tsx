import { useEffect, useState } from "react";
import { AudioLines, Loader2 } from "lucide-react";
import { useAppStore } from "@/stores/appStore";
import { getSpectrogram } from "@/lib/api";

export function SpectrogramView() {
  const audioBlob = useAppStore((s) => s.audioBlob);
  const viewMode = useAppStore((s) => s.viewMode);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!audioBlob) {
      setImageUrl(null);
      return;
    }

    let cancelled = false;

    async function fetchSpec() {
      setLoading(true);
      setError(null);
      try {
        const mode =
          viewMode === "spectrogram"
            ? "power"
            : viewMode === "mel"
            ? "mel"
            : "stft";
        const data = await getSpectrogram(audioBlob!, mode);
        if (!cancelled) {
          setImageUrl(`data:image/png;base64,${data.image_base64}`);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to generate spectrogram");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchSpec();
    return () => {
      cancelled = true;
    };
  }, [audioBlob, viewMode]);

  if (!audioBlob) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 bg-base rounded-lg border border-surface1 m-2 min-h-[200px]">
        <AudioLines size={48} className="text-surface2" />
        <p className="text-subtext text-sm">
          Record or import audio to view the spectrogram
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 bg-base rounded-lg border border-surface1 m-2 min-h-[200px]">
        <Loader2 size={32} className="animate-spin text-primary" />
        <p className="text-subtext text-sm">Generating spectrogram...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 bg-base rounded-lg border border-surface1 m-2 min-h-[200px]">
        <p className="text-red text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-base rounded-lg border border-surface1 m-2 overflow-hidden min-h-[200px]">
      {imageUrl && (
        <img
          src={imageUrl}
          alt="Spectrogram"
          className="w-full h-full object-contain"
        />
      )}
    </div>
  );
}
