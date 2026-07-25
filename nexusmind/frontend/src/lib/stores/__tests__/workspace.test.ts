import { describe, it, expect, beforeEach } from "vitest";
import { useWorkspaceStore } from "../workspace";
import type { WorkspaceFile, EditorTab } from "../workspace";

// Reset store before each test
beforeEach(() => {
  useWorkspaceStore.getState().reset();
});

describe("WorkspaceStore", () => {
  describe("File Management", () => {
    it("should open a file", () => {
      const file: WorkspaceFile = {
        id: "file-1",
        name: "test.ts",
        path: "/src/test.ts",
        content: "const test = 1;",
        language: "typescript",
        modified: false,
      };

      useWorkspaceStore.getState().openFile(file);

      const state = useWorkspaceStore.getState();
      expect(state.openFiles).toHaveLength(1);
      expect(state.openFiles[0].id).toBe("file-1");
      expect(state.activeFileId).toBe("file-1");
    });

    it("should not duplicate files when opening same file", () => {
      const file: WorkspaceFile = {
        id: "file-1",
        name: "test.ts",
        path: "/src/test.ts",
        content: "const test = 1;",
        language: "typescript",
        modified: false,
      };

      useWorkspaceStore.getState().openFile(file);
      useWorkspaceStore.getState().openFile(file);

      const state = useWorkspaceStore.getState();
      expect(state.openFiles).toHaveLength(1);
    });

    it("should close a file", () => {
      const file: WorkspaceFile = {
        id: "file-1",
        name: "test.ts",
        path: "/src/test.ts",
        content: "const test = 1;",
        language: "typescript",
        modified: false,
      };

      useWorkspaceStore.getState().openFile(file);
      useWorkspaceStore.getState().closeFile("file-1");

      const state = useWorkspaceStore.getState();
      expect(state.openFiles).toHaveLength(0);
    });

    it("should update file content", () => {
      const file: WorkspaceFile = {
        id: "file-1",
        name: "test.ts",
        path: "/src/test.ts",
        content: "const test = 1;",
        language: "typescript",
        modified: false,
      };

      useWorkspaceStore.getState().openFile(file);
      useWorkspaceStore.getState().updateFile("file-1", { content: "const test = 2;", modified: true });

      const state = useWorkspaceStore.getState();
      expect(state.openFiles[0].content).toBe("const test = 2;");
      expect(state.openFiles[0].modified).toBe(true);
    });
  });

  describe("Tab Management", () => {
    it("should open a tab", () => {
      const tab: EditorTab = {
        id: "tab-1",
        title: "Test",
        type: "editor",
        pinned: false,
        closable: true,
        fileId: "file-1",
      };

      useWorkspaceStore.getState().openTab(tab);

      const state = useWorkspaceStore.getState();
      expect(state.tabs).toHaveLength(1);
      expect(state.activeTabId).toBe("tab-1");
    });

    it("should close a tab", () => {
      const tab: EditorTab = {
        id: "tab-1",
        title: "Test",
        type: "editor",
        pinned: false,
        closable: true,
        fileId: "file-1",
      };

      useWorkspaceStore.getState().openTab(tab);
      useWorkspaceStore.getState().closeTab("tab-1");

      const state = useWorkspaceStore.getState();
      expect(state.tabs).toHaveLength(0);
    });

    it("should pin and unpin tabs", () => {
      const tab: EditorTab = {
        id: "tab-1",
        title: "Test",
        type: "editor",
        pinned: false,
        closable: true,
      };

      useWorkspaceStore.getState().openTab(tab);
      useWorkspaceStore.getState().pinTab("tab-1");

      let state = useWorkspaceStore.getState();
      expect(state.tabs[0].pinned).toBe(true);

      useWorkspaceStore.getState().unpinTab("tab-1");
      state = useWorkspaceStore.getState();
      expect(state.tabs[0].pinned).toBe(false);
    });

    it("should reorder tabs", () => {
      const tab1: EditorTab = { id: "tab-1", title: "File 1", type: "editor", pinned: false, closable: true };
      const tab2: EditorTab = { id: "tab-2", title: "File 2", type: "editor", pinned: false, closable: true };
      const tab3: EditorTab = { id: "tab-3", title: "File 3", type: "editor", pinned: false, closable: true };

      useWorkspaceStore.getState().openTab(tab1);
      useWorkspaceStore.getState().openTab(tab2);
      useWorkspaceStore.getState().openTab(tab3);
      useWorkspaceStore.getState().reorderTabs(0, 2);

      const state = useWorkspaceStore.getState();
      expect(state.tabs[0].id).toBe("tab-2");
      expect(state.tabs[1].id).toBe("tab-3");
      expect(state.tabs[2].id).toBe("tab-1");
    });

    it("should close other tabs", () => {
      const tab1: EditorTab = { id: "tab-1", title: "File 1", type: "editor", pinned: false, closable: true };
      const tab2: EditorTab = { id: "tab-2", title: "File 2", type: "editor", pinned: false, closable: true };
      const tab3: EditorTab = { id: "tab-3", title: "File 3", type: "editor", pinned: false, closable: true };

      useWorkspaceStore.getState().openTab(tab1);
      useWorkspaceStore.getState().openTab(tab2);
      useWorkspaceStore.getState().openTab(tab3);
      useWorkspaceStore.getState().closeOtherTabs("tab-2");

      const state = useWorkspaceStore.getState();
      expect(state.tabs).toHaveLength(1);
      expect(state.tabs[0].id).toBe("tab-2");
    });

    it("should close all tabs but keep pinned", () => {
      const tab1: EditorTab = { id: "tab-1", title: "File 1", type: "editor", pinned: false, closable: true };
      const tab2: EditorTab = { id: "tab-2", title: "File 2", type: "editor", pinned: true, closable: true };

      useWorkspaceStore.getState().openTab(tab1);
      useWorkspaceStore.getState().openTab(tab2);
      useWorkspaceStore.getState().closeAllTabs();

      const state = useWorkspaceStore.getState();
      expect(state.tabs).toHaveLength(1);
      expect(state.tabs[0].pinned).toBe(true);
    });
  });

  describe("Search", () => {
    it("should set search query", () => {
      useWorkspaceStore.getState().setSearchQuery({
        query: "test",
        regex: false,
        caseSensitive: false,
        wholeWord: false,
        includeHidden: false,
        maxResults: 100,
      });

      const state = useWorkspaceStore.getState();
      expect(state.searchQuery?.query).toBe("test");
    });

    it("should set search results", () => {
      useWorkspaceStore.getState().setSearchResults([
        {
          fileId: "file-1",
          filePath: "/src/test.ts",
          line: 1,
          column: 1,
          match: "test",
          context: "const test = 1;",
        },
      ]);

      const state = useWorkspaceStore.getState();
      expect(state.searchResults).toHaveLength(1);
    });
  });

  describe("Recently Opened", () => {
    it("should add files to recently opened", () => {
      useWorkspaceStore.getState().addToRecentlyOpened("file-1");
      useWorkspaceStore.getState().addToRecentlyOpened("file-2");
      useWorkspaceStore.getState().addToRecentlyOpened("file-3");

      const state = useWorkspaceStore.getState();
      expect(state.recentlyOpened).toEqual(["file-3", "file-2", "file-1"]);
    });

    it("should not duplicate recently opened files", () => {
      useWorkspaceStore.getState().addToRecentlyOpened("file-1");
      useWorkspaceStore.getState().addToRecentlyOpened("file-2");
      useWorkspaceStore.getState().addToRecentlyOpened("file-1");

      const state = useWorkspaceStore.getState();
      expect(state.recentlyOpened).toEqual(["file-1", "file-2"]);
    });

    it("should limit recently opened to 20 files", () => {
      for (let i = 0; i < 25; i++) {
        useWorkspaceStore.getState().addToRecentlyOpened(`file-${i}`);
      }

      const state = useWorkspaceStore.getState();
      expect(state.recentlyOpened).toHaveLength(20);
    });
  });

  describe("Reset", () => {
    it("should reset all state", () => {
      const file: WorkspaceFile = {
        id: "file-1",
        name: "test.ts",
        path: "/src/test.ts",
        content: "const test = 1;",
        language: "typescript",
        modified: false,
      };

      useWorkspaceStore.getState().openFile(file);
      useWorkspaceStore.getState().addToRecentlyOpened("file-1");
      useWorkspaceStore.getState().reset();

      const state = useWorkspaceStore.getState();
      expect(state.openFiles).toHaveLength(0);
      expect(state.tabs).toHaveLength(0);
      expect(state.recentlyOpened).toHaveLength(0);
    });
  });
});

describe("WorkspaceFile", () => {
  it("should create a valid workspace file", () => {
    const file: WorkspaceFile = {
      id: "file-1",
      name: "test.ts",
      path: "/src/test.ts",
      content: "const test = 1;",
      language: "typescript",
      modified: false,
    };

    expect(file.id).toBe("file-1");
    expect(file.name).toBe("test.ts");
    expect(file.modified).toBe(false);
  });
});

describe("EditorTab", () => {
  it("should create a valid editor tab", () => {
    const tab: EditorTab = {
      id: "tab-1",
      title: "Test",
      type: "editor",
      pinned: false,
      closable: true,
      fileId: "file-1",
    };

    expect(tab.id).toBe("tab-1");
    expect(tab.type).toBe("editor");
    expect(tab.closable).toBe(true);
  });
});
