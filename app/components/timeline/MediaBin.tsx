import { useOutletContext } from "react-router";
import { useMemo, memo, useState } from "react";
import { FileVideo, FileImage, Type, Clock, Upload, Music, Trash2, SplitSquareHorizontal, X } from "lucide-react";
import { Thumbnail } from '@remotion/player';
import { OffthreadVideo, Img, Video } from 'remotion';
import { type MediaBinItem } from "./types";
import { Badge } from "~/components/ui/badge";
import { Progress } from "~/components/ui/progress";

interface MediaBinProps {
  mediaBinItems: MediaBinItem[];
  onAddMedia: (file: File) => Promise<void>;
  onAddText: (
    textContent: string,
    fontSize: number,
    fontFamily: string,
    color: string,
    textAlign: "left" | "center" | "right",
    fontWeight: "normal" | "bold"
  ) => void;
  contextMenu: {
    x: number;
    y: number;
    item: MediaBinItem;
  } | null;
  handleContextMenu: (e: React.MouseEvent, item: MediaBinItem) => void;
  handleDeleteFromContext: () => Promise<void>;
  handleSplitAudioFromContext: () => Promise<void>;
  handleCloseContextMenu: () => void;
}

// Memoized component for video thumbnails to prevent flickering
const VideoThumbnail = memo(({ 
  mediaUrl, 
  width, 
  height 
}: { 
  mediaUrl: string; 
  width: number; 
  height: number; 
}) => {
  const VideoComponent = useMemo(() => {
    return () => <Video src={mediaUrl} />;
  }, [mediaUrl]);

  return (
    <div className="w-12 h-8 rounded border border-border/50 overflow-hidden bg-card">
      <Thumbnail
        component={VideoComponent}
        compositionWidth={width}
        compositionHeight={height}
        frameToDisplay={30}
        durationInFrames={1}
        fps={30}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </div>
  );
});

// This is required for the data router
export function loader() {
  return null;
}

export default function MediaBin() {
  const { 
    mediaBinItems, 
    onAddMedia, 
    onAddText, 
    contextMenu, 
    handleContextMenu, 
    handleDeleteFromContext, 
    handleSplitAudioFromContext, 
    handleCloseContextMenu 
  } = useOutletContext<MediaBinProps>();

  // State for media preview popup
  const [previewItem, setPreviewItem] = useState<MediaBinItem | null>(null);

  const getMediaIcon = (mediaType: string) => {
    switch (mediaType) {
      case "video":
        return <FileVideo className="h-4 w-4" />;
      case "image":
        return <FileImage className="h-4 w-4" />;
      case "text":
        return <Type className="h-4 w-4" />;
      case "audio":
        return <Music className="h-4 w-4" />;
      default:
        return <FileImage className="h-4 w-4" />;
    }
  };

  const renderThumbnail = (item: MediaBinItem) => {
    const mediaUrl = item.mediaUrlLocal || item.mediaUrlRemote;
    
    // Show icon for uploading items
    if (item.isUploading) {
      return <Upload className="h-8 w-8 animate-pulse text-muted-foreground" />;
    }

    // Show thumbnails for different media types
    switch (item.mediaType) {
      case "video":
        if (mediaUrl) {
          return (
            <VideoThumbnail
              mediaUrl={mediaUrl}
              width={item.media_width || 1920}
              height={item.media_height || 1080}
            />
          );
        }
        return <FileVideo className="h-8 w-8 text-muted-foreground" />;
      
      case "image":
        if (mediaUrl) {
          console.log("🖼️ MediaBin rendering image:", item.name, "URL:", mediaUrl);
          return (
            <div className="w-12 h-8 rounded border border-border/50 overflow-hidden bg-card">
              <img 
                src={mediaUrl} 
                alt={item.name}
                className="w-full h-full object-cover"
                onLoad={() => console.log("✅ Image loaded successfully:", mediaUrl)}
                onError={(e) => {
                  console.error("❌ Image failed to load:", mediaUrl);
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling?.classList.remove('hidden');
                }}
              />
              <FileImage className="h-8 w-8 text-muted-foreground hidden" />
            </div>
          );
        }
        return <FileImage className="h-8 w-8 text-muted-foreground" />;
      
      case "text":
        return (
          <div className="w-12 h-8 rounded border border-border/50 bg-card flex items-center justify-center">
            <Type className="h-4 w-4 text-muted-foreground" />
          </div>
        );
      
      case "audio":
        return (
          <div className="w-12 h-8 rounded border border-border/50 bg-card flex items-center justify-center">
            <Music className="h-4 w-4 text-muted-foreground" />
          </div>
        );
      
      default:
        return <FileImage className="h-8 w-8 text-muted-foreground" />;
    }
  };

  return (
    <div className="h-full flex flex-col bg-background" onClick={handleCloseContextMenu}>
      {/* Compact Header */}
      <div className="p-2 border-b border-border/50">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-medium text-foreground">Media Library</h3>
          <Badge variant="secondary" className="text-xs h-4 px-1.5 font-mono">
            {mediaBinItems.length}
          </Badge>
        </div>
      </div>

      {/* Media Items */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 panel-scrollbar">
        {mediaBinItems.map((item) => (
          <div
            key={item.id}
            className={`group p-2 border border-border/50 rounded-md transition-colors ${
              item.isUploading 
                ? "bg-accent/30 cursor-default" 
                : "bg-card cursor-grab hover:bg-accent/50"
            }`}
            draggable={!item.isUploading}
            onDragStart={(e) => {
              if (!item.isUploading) {
                e.dataTransfer.setData("application/json", JSON.stringify(item));
                // Also store in a global variable for timeline preview
                (window as any).__draggedMediaItem = item;
                
                // Create a custom drag image that's smaller and more transparent
                const dragImage = document.createElement('div');
                dragImage.innerHTML = item.name;
                dragImage.style.cssText = `
                  position: absolute;
                  top: -1000px;
                  left: -1000px;
                  background: rgba(59, 130, 246, 0.8);
                  color: white;
                  padding: 4px 8px;
                  border-radius: 4px;
                  font-size: 12px;
                  font-weight: 500;
                  pointer-events: none;
                  z-index: 1000;
                `;
                document.body.appendChild(dragImage);
                e.dataTransfer.setDragImage(dragImage, 10, 10);
                
                // Clean up the drag image after a short delay
                setTimeout(() => {
                  document.body.removeChild(dragImage);
                }, 0);
                
                console.log("Dragging item:", item.name);
              }
            }}
            onContextMenu={(e) => handleContextMenu(e, item)}
            onClick={(e) => {
              // Only open preview if not dragging and not uploading
              if (!item.isUploading && e.button === 0) {
                setPreviewItem(item);
              }
            }}
          >
            <div className="flex items-start gap-2">
              <div className="flex-shrink-0">
                {renderThumbnail(item)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className={`text-xs font-medium truncate transition-colors ${
                    item.isUploading 
                      ? "text-muted-foreground" 
                      : "text-foreground group-hover:text-accent-foreground"
                  }`}>
                    {item.title || item.name}
                  </p>
                  
                  {item.isUploading && typeof item.uploadProgress === "number" && (
                    <span className="text-xs text-muted-foreground font-mono">
                      {item.uploadProgress}%
                    </span>
                  )}
                </div>

                {/* Upload Progress Bar */}
                {item.isUploading && typeof item.uploadProgress === "number" && (
                  <div className="mt-1 mb-1">
                    <Progress value={item.uploadProgress} className="h-1" />
                  </div>
                )}

                <div className="flex items-center gap-1.5 mt-0.5">
                  <Badge
                    variant="secondary"
                    className="text-xs px-1 py-0 h-auto"
                  >
                    {item.isUploading ? "uploading" : item.mediaType}
                  </Badge>

                  {(item.mediaType === "video" || item.mediaType === "audio") && item.durationInSeconds > 0 && !item.isUploading && (
                    <div className="flex items-center gap-0.5 text-xs text-muted-foreground">
                      <Clock className="h-2.5 w-2.5" />
                      {item.durationInSeconds.toFixed(1)}s
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {mediaBinItems.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <FileImage className="h-8 w-8 text-muted-foreground/50 mb-3" />
            <p className="text-xs text-muted-foreground">No media files</p>
            <p className="text-xs text-muted-foreground/70 mt-0.5">
              Import videos, images, or audio to get started
            </p>
          </div>
        )}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed bg-popover border border-border rounded-md shadow-lg z-50 py-1 min-w-32"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="w-full px-3 py-1.5 text-left text-xs hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
            onClick={handleDeleteFromContext}
          >
            <Trash2 className="h-3 w-3" />
            Delete Media
          </button>
          {contextMenu.item.mediaType === 'video' && (
            <button
              className="w-full px-3 py-1.5 text-left text-xs hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
              onClick={handleSplitAudioFromContext}
            >
              <SplitSquareHorizontal className="h-3 w-3" />
              Split Audio
            </button>
          )}
        </div>
      )}

      {/* Media Preview Modal */}
      {previewItem && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60]"
          onClick={() => setPreviewItem(null)}
        >
          <div 
            className="bg-card border border-border rounded-lg shadow-2xl max-w-4xl max-h-[90vh] w-full mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
              <div className="flex items-center gap-3">
                {getMediaIcon(previewItem.mediaType)}
                <div>
                  <h3 className="text-sm font-semibold text-foreground">
                    {previewItem.title || previewItem.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge variant="secondary" className="text-xs">
                      {previewItem.mediaType}
                    </Badge>
                    {previewItem.media_width && previewItem.media_height && (
                      <span className="text-xs text-muted-foreground">
                        {previewItem.media_width} × {previewItem.media_height}
                      </span>
                    )}
                    {previewItem.durationInSeconds > 0 && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {previewItem.durationInSeconds.toFixed(1)}s
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Preview Content */}
            <div className="p-4 max-h-[calc(90vh-80px)] overflow-auto">
              {previewItem.mediaType === 'video' && (
                <video
                  src={previewItem.mediaUrlLocal || previewItem.mediaUrlRemote || ''}
                  controls
                  autoPlay
                  className="w-full rounded border border-border bg-black"
                  style={{ maxHeight: 'calc(90vh - 200px)' }}
                />
              )}
              {previewItem.mediaType === 'image' && (
                <img
                  src={previewItem.mediaUrlLocal || previewItem.mediaUrlRemote || ''}
                  alt={previewItem.name}
                  className="w-full rounded border border-border"
                  style={{ maxHeight: 'calc(90vh - 200px)', objectFit: 'contain' }}
                />
              )}
              {previewItem.mediaType === 'audio' && (
                <div className="flex flex-col items-center justify-center py-12">
                  <Music className="h-16 w-16 text-muted-foreground mb-4" />
                  <audio
                    src={previewItem.mediaUrlLocal || previewItem.mediaUrlRemote || ''}
                    controls
                    autoPlay
                    className="w-full max-w-md"
                  />
                </div>
              )}
              {previewItem.mediaType === 'text' && previewItem.text && (
                <div className="flex items-center justify-center min-h-[300px] bg-muted/20 rounded border border-border">
                  <p
                    style={{
                      fontSize: `${previewItem.text.fontSize}px`,
                      fontFamily: previewItem.text.fontFamily,
                      color: previewItem.text.color,
                      textAlign: previewItem.text.textAlign,
                      fontWeight: previewItem.text.fontWeight,
                    }}
                    className="px-8"
                  >
                    {previewItem.text.textContent}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
