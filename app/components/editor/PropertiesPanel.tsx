import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router";
import { Card, CardContent } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  ChevronRight,
  ChevronDown,
  FileCode,
  Box,
  Type as TypeIcon,
  Image as ImageIcon,
  Layout,
  Save,
} from "lucide-react";
import { parseElementString } from "../../utils/transformUtils";
import type { CompositionBlueprint, Clip } from "../../video-compositions/BlueprintTypes";

interface PropertiesPanelContext {
  selectedClipId: string | null;
  currentComposition: CompositionBlueprint;
  onUpdateClipElements: (clipId: string, newElements: string[]) => void;
}

interface ParsedElement {
  tag: string;
  id: string;
  parent: string;
  props: Record<string, string | undefined>;
  children: ParsedElement[];
  originalIndex: number;
}

export default function PropertiesPanel() {
  const { selectedClipId, currentComposition, onUpdateClipElements } =
    useOutletContext<PropertiesPanelContext>();

  const [elementTree, setElementTree] = useState<ParsedElement[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [editedValues, setEditedValues] = useState<
    Map<string, Record<string, string>>
  >(new Map());
  const [hasChanges, setHasChanges] = useState(false);

  // Parse elements when selected clip changes
  useEffect(() => {
    if (!selectedClipId || !currentComposition) {
      setElementTree([]);
      setEditedValues(new Map());
      setHasChanges(false);
      return;
    }

    // Find the selected clip
    let selectedClip: Clip | null = null;
    for (const track of currentComposition) {
      const clip = track.clips.find((c) => c.id === selectedClipId);
      if (clip) {
        selectedClip = clip;
        break;
      }
    }

    if (!selectedClip) {
      setElementTree([]);
      return;
    }

    // Parse elements into a tree structure
    const parsedElements: ParsedElement[] = selectedClip.element.elements.map(
      (elementStr, index) => {
        const parsed = parseElementString(elementStr);
        const { tag, id, parent, ...otherProps } = parsed;
        return {
          tag,
          id: id || `element-${index}`,
          parent: parent || "root",
          props: otherProps,
          children: [],
          originalIndex: index,
        };
      }
    );

    // Build tree by linking children to parents
    const elementMap = new Map<string, ParsedElement>();
    parsedElements.forEach((el) => elementMap.set(el.id, el));

    const rootElements: ParsedElement[] = [];
    parsedElements.forEach((el) => {
      if (el.parent === "root" || !elementMap.has(el.parent)) {
        rootElements.push(el);
      } else {
        const parent = elementMap.get(el.parent);
        if (parent) {
          parent.children.push(el);
        }
      }
    });

    setElementTree(rootElements);

    // Auto-expand root nodes
    const autoExpand = new Set<string>();
    rootElements.forEach((el) => autoExpand.add(el.id));
    setExpandedNodes(autoExpand);
  }, [selectedClipId, currentComposition]);

  const toggleExpand = (elementId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(elementId)) {
        next.delete(elementId);
      } else {
        next.add(elementId);
      }
      return next;
    });
  };

  const handlePropertyChange = (
    elementId: string,
    propKey: string,
    value: string
  ) => {
    setEditedValues((prev) => {
      const next = new Map(prev);
      const elementEdits = next.get(elementId) || {};
      next.set(elementId, { ...elementEdits, [propKey]: value });
      return next;
    });
    setHasChanges(true);
  };

  const handleSaveChanges = () => {
    if (!selectedClipId || !currentComposition) return;

    // Find the selected clip
    let selectedClip: Clip | null = null;
    for (const track of currentComposition) {
      const clip = track.clips.find((c) => c.id === selectedClipId);
      if (clip) {
        selectedClip = clip;
        break;
      }
    }

    if (!selectedClip) return;

    // Apply edits to elements
    const updatedElements = selectedClip.element.elements.map((elementStr) => {
      const parsed = parseElementString(elementStr);
      const edits = parsed.id ? editedValues.get(parsed.id) : undefined;

      if (!edits) return elementStr;

      // Apply edits to props
      const { tag, id, parent, ...otherProps } = parsed;
      const updatedProps = { ...otherProps, ...edits };

      // Rebuild element string
      const parts = [
        tag,
        `id:${id || ""}`,
        `parent:${parent || "root"}`,
      ];

      Object.entries(updatedProps).forEach(([key, value]) => {
        if (value !== undefined) {
          parts.push(`${key}:${value}`);
        }
      });

      return parts.join(";");
    });

    // Update the clip
    onUpdateClipElements(selectedClipId, updatedElements);
    setEditedValues(new Map());
    setHasChanges(false);
  };

  const getElementIcon = (tag: string) => {
    switch (tag.toLowerCase()) {
      case "div":
        return <Box className="h-3.5 w-3.5" />;
      case "p":
      case "span":
        return <TypeIcon className="h-3.5 w-3.5" />;
      case "img":
        return <ImageIcon className="h-3.5 w-3.5" />;
      default:
        return <Layout className="h-3.5 w-3.5" />;
    }
  };

  const renderElement = (element: ParsedElement, depth: number = 0) => {
    const isExpanded = expandedNodes.has(element.id);
    const hasChildren = element.children.length > 0;
    const elementEdits = editedValues.get(element.id) || {};
    const displayProps = { ...element.props, ...elementEdits };

    return (
      <div key={element.id} className="space-y-1">
        {/* Element Header */}
        <div
          className="flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-muted/50 cursor-pointer"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {hasChildren && (
            <button
              onClick={() => toggleExpand(element.id)}
              className="p-0 hover:bg-transparent"
            >
              {isExpanded ? (
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-3.5" />}

          {getElementIcon(element.tag)}

          <span className="text-sm font-medium">
            {element.tag}
            <span className="text-xs text-muted-foreground ml-1.5">
              #{element.id}
            </span>
          </span>

          {element.children.length > 0 && (
            <Badge variant="outline" className="text-xs">
              {element.children.length}
            </Badge>
          )}
        </div>

        {/* Element Properties */}
        {isExpanded && (
          <div
            className="space-y-2 py-2 border-l-2 border-border/50"
            style={{ marginLeft: `${depth * 16 + 20}px` }}
          >
            {Object.entries(displayProps).length > 0 ? (
              <div className="grid gap-2 px-3">
                {Object.entries(displayProps).map(([key, value]) => (
                  <div key={key} className="grid gap-1">
                    <Label className="text-xs text-muted-foreground">
                      {key}
                    </Label>
                    <Input
                      value={value}
                      onChange={(e) =>
                        handlePropertyChange(element.id, key, e.target.value)
                      }
                      className="h-7 text-xs font-mono"
                      placeholder={`Enter ${key}`}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground px-3">
                No properties
              </p>
            )}
          </div>
        )}

        {/* Render Children */}
        {isExpanded &&
          element.children.map((child) => renderElement(child, depth + 1))}
      </div>
    );
  };

  if (!selectedClipId) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center">
        <FileCode className="h-12 w-12 text-muted-foreground/50 mb-3" />
        <p className="text-sm text-muted-foreground">
          Select a clip to view its properties
        </p>
      </div>
    );
  }

  if (elementTree.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center">
        <FileCode className="h-12 w-12 text-muted-foreground/50 mb-3" />
        <p className="text-sm text-muted-foreground">
          No elements found in this clip
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCode className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-medium">Element Properties</h3>
          </div>
          {hasChanges && (
            <Button
              size="sm"
              onClick={handleSaveChanges}
              className="h-7 text-xs gap-1.5"
            >
              <Save className="h-3 w-3" />
              Save
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Clip: {selectedClipId}
        </p>
      </div>

      {/* Element Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        <Card className="border-border/50">
          <CardContent className="p-2">
            {elementTree.map((element) => renderElement(element, 0))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
