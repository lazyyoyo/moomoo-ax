"use client";

import { Suspense, useState, useEffect, useRef, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ImagePlus, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { copy } from "@/lib/copy";
import { api } from "@/lib/api-client";
import { createClient } from "@/lib/supabase/client";
import { useToast } from "@/components/shared/toast";
import { BookCover } from "@/components/shared/book-cover";
import type {
  AladinItem,
  AladinSearchResult,
  AddBookAladinRequest,
  AddBookManualRequest,
} from "@/lib/types";

type ViewState = "idle" | "loading" | "results" | "no-results" | "error";
type AddStatus = "idle" | "adding" | "added" | "error";

interface LibraryBook {
  isbn: string;
  catalog_book_id: string;
  user_book_id: string;
  task_id: string | null;
  task_status: string | null;
}

type SearchIntent = "reading" | "want-to-read" | null;

function getIntent(raw: string | null): SearchIntent {
  if (raw === "reading" || raw === "want-to-read") return raw;
  return null;
}

export default function SearchPage() {
  return (
    <Suspense>
      <SearchPageContent />
    </Suspense>
  );
}

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const intent = getIntent(searchParams.get("intent"));
  const toast = useToast();

  const [query, setQuery] = useState("");
  const [bookType, setBookType] = useState<"Book" | "eBook" | "Foreign">("Book");
  const [viewState, setViewState] = useState<ViewState>("idle");
  const [results, setResults] = useState<AladinItem[]>([]);
  const [addStatuses, setAddStatuses] = useState<Record<string, AddStatus>>({});
  const [showManual, setShowManual] = useState(false);
  const [libraryMap, setLibraryMap] = useState<Record<string, LibraryBook>>({});
  const [intentStatuses, setIntentStatuses] = useState<Record<string, AddStatus>>({});
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 서재 ISBN 프리페치
  useEffect(() => {
    (async () => {
      const { data } = await api.get<{ items: LibraryBook[] }>("/api/books/isbns");
      if (data?.items) {
        const map: Record<string, LibraryBook> = {};
        for (const item of data.items) map[item.isbn] = item;
        setLibraryMap(map);
      }
    })();
  }, []);

  const search = useCallback(async (q: string, type: "Book" | "eBook" | "Foreign" = "Book") => {
    if (!q.trim()) {
      setViewState("idle");
      setResults([]);
      return;
    }
    setViewState("loading");
    const { data, error } = await api.get<AladinSearchResult>(
      `/api/search?query=${encodeURIComponent(q.trim())}&type=${type}`
    );
    if (error || !data) {
      setViewState("error");
      return;
    }
    setResults(data.items);
    setViewState(data.items.length === 0 ? "no-results" : "results");
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(query, bookType), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, bookType, search]);

  const handleIntentAdd = async (isbn: string, lib: LibraryBook) => {
    if (!intent) return;
    setIntentStatuses((prev) => ({ ...prev, [isbn]: "adding" }));

    const today = new Date().toISOString().split("T")[0];

    // todo → in_progress 전환 (PATCH)
    if (intent === "reading" && lib.task_status === "todo" && lib.task_id) {
      const { error: patchError } = await api.patch(
        `/api/reading-tasks/${lib.task_id}`,
        { status: "in_progress", start_date: today }
      );
      if (patchError) {
        setIntentStatuses((prev) => ({ ...prev, [isbn]: "error" }));
        return;
      }
      // libraryMap 업데이트
      setLibraryMap((prev) => ({
        ...prev,
        [isbn]: { ...lib, task_status: "in_progress" },
      }));
      setIntentStatuses((prev) => ({ ...prev, [isbn]: "added" }));
      toast.show(copy.search.intentReadingSuccess);
      return;
    }

    // 새 task 생성
    const taskStatus = intent === "reading" ? "in_progress" : "todo";
    const taskBody: Record<string, unknown> = {
      catalog_book_id: lib.catalog_book_id,
      status: taskStatus,
    };
    if (intent === "reading") taskBody.start_date = today;

    const { error: taskError } = await api.post("/api/reading-tasks", taskBody);
    if (taskError) {
      setIntentStatuses((prev) => ({ ...prev, [isbn]: "error" }));
      return;
    }

    setLibraryMap((prev) => ({
      ...prev,
      [isbn]: { ...lib, task_status: taskStatus },
    }));
    setIntentStatuses((prev) => ({ ...prev, [isbn]: "added" }));
    toast.show(
      intent === "reading"
        ? copy.search.intentReadingSuccess
        : copy.search.intentWantToReadSuccess
    );
  };

  const handleTabChange = (type: "Book" | "eBook" | "Foreign") => {
    setBookType(type);
    setAddStatuses({});
  };

  const handleAdd = async (item: AladinItem) => {
    const key = item.isbn13;
    setAddStatuses((prev) => ({ ...prev, [key]: "adding" }));

    let totalPages: number | null = null;
    if (item.isbn13) {
      const { data: lookupData } = await api.get<{ totalPages: number | null }>(
        `/api/search/lookup?isbn=${item.isbn13}`
      );
      if (lookupData?.totalPages) totalPages = lookupData.totalPages;
    }

    const body: AddBookAladinRequest = {
      type: "aladin",
      title: item.title,
      subtitle: item.subtitle,
      title_raw: item.titleRaw || null,
      author: item.author || null,
      translator: item.translator,
      artist: item.artist,
      author_raw: item.authorRaw || null,
      publisher: item.publisher || null,
      published_date: item.pubDate || null,
      cover_url: item.cover || null,
      isbn: item.isbn13,
      category: item.category.length > 0 ? item.category : null,
      total_pages: totalPages,
      book_type: item.mallType || null,
    };

    const { data: bookData, error, meta } = await api.post<{ id: string; catalog_book_id: string }>("/api/books", body);

    if (error) {
      if (error.includes(copy.library.bookAlreadyExists) && meta?.catalog_book_id) {
        // 이미 서재에 있음 — libraryMap에 없으면 추가
        if (!libraryMap[item.isbn13]) {
          setLibraryMap((prev) => ({
            ...prev,
            [item.isbn13]: {
              isbn: item.isbn13,
              catalog_book_id: meta.catalog_book_id as string,
              user_book_id: "",
              task_id: null,
              task_status: null,
            },
          }));
        }
        setAddStatuses((prev) => ({ ...prev, [key]: "added" }));
      } else {
        setAddStatuses((prev) => ({ ...prev, [key]: "error" }));
      }
      return;
    }

    const catalogBookId = bookData?.catalog_book_id ?? meta?.catalog_book_id;

    // intent 모드: 서재 등록 + task 생성을 한 번에 처리 후 libraryMap 업데이트
    if (intent && catalogBookId) {
      const taskStatus = intent === "reading" ? "in_progress" : "todo";
      const today = new Date().toISOString().split("T")[0];
      const taskBody: Record<string, unknown> = {
        catalog_book_id: catalogBookId,
        status: taskStatus,
      };
      if (intent === "reading") taskBody.start_date = today;

      const { error: taskError } = await api.post("/api/reading-tasks", taskBody);
      if (taskError) {
        if (taskError.includes("409") || taskError.includes("이미")) {
          toast.show(
            intent === "reading"
              ? copy.search.intentReadingDuplicate
              : copy.search.intentWantToReadDuplicate
          );
        } else {
          toast.show(copy.search.intentPartialSuccess);
        }
        // 서재 등록은 됐으므로 libraryMap 업데이트 (task 없이)
        if (bookData) {
          setLibraryMap((prev) => ({
            ...prev,
            [item.isbn13]: {
              isbn: item.isbn13,
              catalog_book_id: bookData.catalog_book_id,
              user_book_id: bookData.id,
              task_id: null,
              task_status: null,
            },
          }));
        }
        setAddStatuses((prev) => ({ ...prev, [key]: "added" }));
        return;
      }

      // 성공: 서재 + task 한 번에 libraryMap 반영 (깜빡임 방지)
      setLibraryMap((prev) => ({
        ...prev,
        [item.isbn13]: {
          isbn: item.isbn13,
          catalog_book_id: (catalogBookId as string),
          user_book_id: bookData?.id ?? "",
          task_id: null,
          task_status: taskStatus,
        },
      }));
      setAddStatuses((prev) => ({ ...prev, [key]: "added" }));
      toast.show(
        intent === "reading"
          ? copy.search.intentReadingSuccess
          : copy.search.intentWantToReadSuccess
      );
      return;
    }

    // 기본 검색 (intent 없음): 서재 등록만
    if (bookData) {
      setLibraryMap((prev) => ({
        ...prev,
        [item.isbn13]: {
          isbn: item.isbn13,
          catalog_book_id: bookData.catalog_book_id,
          user_book_id: bookData.id,
          task_id: null,
          task_status: null,
        },
      }));
    }
    setAddStatuses((prev) => ({ ...prev, [key]: "added" }));
    toast.show(copy.library.bookAdded);
  };

  return (
    <div style={{ paddingTop: 28, paddingBottom: 48 }}>
      {/* 뒤로 */}
      <button
        onClick={() => router.back()}
        className="inline-block text-[13px]"
        style={{
          color: "var(--coral-text-sub)",
          marginBottom: 20,
          background: "none",
          border: "none",
          cursor: "pointer",
        }}
      >
        ← {copy.common.back}
      </button>

      <h1
        className="text-[20px] font-semibold"
        style={{ marginBottom: 16 }}
      >
        {intent === "reading"
          ? copy.search.intentReadingTitle
          : intent === "want-to-read"
            ? copy.search.intentWantToReadTitle
            : copy.search.title}
      </h1>

      {/* 종이책/전자책/외국도서 탭 */}
      <div
        className="flex"
        style={{
          borderBottom: "1px solid var(--coral-border)",
          marginBottom: 16,
        }}
      >
        {(
          [
            { key: "Book" as const, label: copy.book.tabBook },
            { key: "eBook" as const, label: copy.book.tabEbook },
            { key: "Foreign" as const, label: copy.book.tabForeign },
          ] as const
        ).map((tab) => {
          const isActive = tab.key === bookType;
          return (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key)}
              className="text-[13px] font-medium"
              style={{
                padding: "8px 16px",
                color: isActive
                  ? "var(--coral-accent)"
                  : "var(--coral-text-muted)",
                borderBottom: isActive
                  ? "2px solid var(--coral-accent)"
                  : "2px solid transparent",
                marginBottom: -1,
                transition:
                  "color var(--coral-transition), border-color var(--coral-transition)",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 검색 입력 */}
      <div style={{ marginBottom: 24 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={copy.search.placeholder}
          className="w-full text-[14px] outline-none"
          style={{
            padding: "11px 14px",
            border: "1px solid var(--coral-border)",
            borderRadius: "var(--coral-radius)",
            backgroundColor: "var(--coral-surface)",
            maxWidth: 480,
            transition: "border-color var(--coral-transition)",
          }}
          onFocus={(e) =>
            (e.currentTarget.style.borderColor = "var(--coral-accent)")
          }
          onBlur={(e) =>
            (e.currentTarget.style.borderColor = "var(--coral-border)")
          }
        />
      </div>

      {/* 초기 */}
      {viewState === "idle" && (
        <p
          className="text-[14px]"
          style={{ color: "var(--coral-text-muted)", paddingTop: 8 }}
        >
          {copy.search.placeholder}
        </p>
      )}

      {/* 로딩 */}
      {viewState === "loading" && (
        <div className="flex flex-col">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-start animate-pulse"
              style={{
                gap: 12,
                padding: "12px 0",
                borderBottom: "1px solid var(--coral-border)",
              }}
            >
              <div
                style={{
                  width: 56,
                  height: 80,
                  borderRadius: "var(--coral-radius-cover)",
                  backgroundColor: "var(--coral-border)",
                }}
              />
              <div className="flex-1">
                <div
                  className="h-3.5 w-2/3 rounded"
                  style={{ backgroundColor: "var(--coral-border)", marginBottom: 6 }}
                />
                <div
                  className="h-3 w-1/3 rounded"
                  style={{ backgroundColor: "var(--coral-border)" }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 에러 */}
      {viewState === "error" && (
        <div className="py-20 text-center">
          <p
            className="text-[13px]"
            style={{ color: "var(--coral-error)" }}
          >
            {copy.search.errorSearch}
          </p>
          <button
            onClick={() => search(query, bookType)}
            className="mt-4 text-[13px] font-medium"
            style={{
              padding: "7px 16px",
              backgroundColor: "var(--coral-accent)",
              color: "var(--primary-foreground)",
              borderRadius: "var(--coral-radius-sm)",
            }}
          >
            {copy.common.retry}
          </button>
        </div>
      )}

      {/* 결과 없음 */}
      {viewState === "no-results" && (
        <div className="py-20 text-center">
          <p
            className="text-[14px] font-medium"
            style={{ color: "var(--coral-text)" }}
          >
            {copy.search.noResults}
          </p>
          <button
            onClick={() => setShowManual(true)}
            className="mt-3 text-[13px] font-medium"
            style={{
              color: "var(--coral-accent)",
              background: "none",
              border: "none",
              cursor: "pointer",
            }}
          >
            {copy.search.manualEntry}
          </button>
        </div>
      )}

      {/* 결과 */}
      {viewState === "results" && (
        <>
          <div className="flex flex-col">
            {results.map((item, index) => {
              const key = item.isbn13 || `search-${index}`;
              const status = addStatuses[item.isbn13] ?? "idle";
              const lib = libraryMap[item.isbn13];
              const inLibrary = !!lib;

              return (
                <div
                  key={key}
                  className="flex items-start"
                  style={{
                    gap: 12,
                    padding: "12px 0",
                    borderBottom: "1px solid var(--coral-border)",
                  }}
                >
                  {inLibrary ? (
                    <Link href={`/books/${lib.user_book_id}`} className="shrink-0">
                      <BookCover src={item.cover || null} alt={item.title} height={80} />
                    </Link>
                  ) : (
                    <BookCover src={item.cover || null} alt={item.title} height={80} />
                  )}

                  <div className="flex-1 min-w-0" style={{ paddingTop: 2 }}>
                    {inLibrary ? (
                      <Link href={`/books/${lib.user_book_id}`}>
                        <p
                          className="text-[14px] font-medium line-clamp-2"
                          style={{ color: "var(--coral-text)" }}
                        >
                          {item.title}
                        </p>
                      </Link>
                    ) : (
                      <p
                        className="text-[14px] font-medium line-clamp-2"
                        style={{ color: "var(--coral-text)" }}
                      >
                        {item.title}
                      </p>
                    )}
                    {item.subtitle && (
                      <p
                        className="text-[12px] line-clamp-1 mt-[1px]"
                        style={{ color: "var(--coral-text-muted)" }}
                      >
                        {item.subtitle}
                      </p>
                    )}
                    <p
                      className="text-[13px] line-clamp-1 mt-[2px]"
                      style={{ color: "var(--coral-text-sub)" }}
                    >
                      {item.author}
                    </p>
                    <p
                      className="text-[12px] mt-[1px]"
                      style={{ color: "var(--coral-text-muted)" }}
                    >
                      {item.publisher}
                    </p>
                    {inLibrary && (
                      <p
                        className="text-[12px] mt-[2px]"
                        style={{ color: "var(--coral-text-muted)" }}
                      >
                        {copy.search.inLibraryBadge}
                      </p>
                    )}
                  </div>

                  {inLibrary ? (
                    (() => {
                      if (!intent) {
                        // 기본 검색: "등록됨" → 책 상세
                        return (
                          <Link
                            href={`/books/${lib.user_book_id}`}
                            className="shrink-0 inline-flex items-center text-[13px] font-medium"
                            style={{
                              padding: "6px 14px",
                              borderRadius: "var(--coral-radius-sm)",
                              border: "1px solid var(--coral-border)",
                              backgroundColor: "var(--coral-bg)",
                              color: "var(--coral-text-muted)",
                              marginTop: 2,
                              gap: 4,
                              textDecoration: "none",
                            }}
                          >
                            {copy.search.added}
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.5 }}>
                              <path d="m9 18 6-6-6-6" />
                            </svg>
                          </Link>
                        );
                      }

                      // intent 모드: 이미 해당 상태면 비활성
                      const ts = lib.task_status;
                      const alreadyReading = ts === "in_progress";
                      const alreadyTodo = ts === "todo";
                      const isDisabled =
                        (intent === "reading" && alreadyReading) ||
                        (intent === "want-to-read" && alreadyTodo) ||
                        (intent === "want-to-read" && alreadyReading);

                      if (isDisabled) {
                        return (
                          <span
                            className="shrink-0 text-[13px] font-medium"
                            style={{
                              padding: "6px 14px",
                              borderRadius: "var(--coral-radius-sm)",
                              border: "1px solid var(--coral-border)",
                              color: "var(--coral-text-muted)",
                              marginTop: 2,
                            }}
                          >
                            {alreadyReading
                              ? copy.search.intentReadingAlready
                              : copy.search.intentWantToReadAlready}
                          </span>
                        );
                      }

                      // 액션 가능 (task 없음, done, dropped, todo→reading)
                      const iStatus = intentStatuses[item.isbn13] ?? "idle";
                      return (
                        <button
                          onClick={() => handleIntentAdd(item.isbn13, lib)}
                          disabled={iStatus === "adding" || iStatus === "added"}
                          className="shrink-0 text-[13px] font-medium"
                          style={{
                            padding: "6px 14px",
                            borderRadius: "var(--coral-radius-sm)",
                            border: iStatus === "added"
                              ? "1px solid var(--coral-border)"
                              : "1px solid var(--coral-accent)",
                            backgroundColor: "transparent",
                            color: iStatus === "added"
                              ? "var(--coral-text-muted)"
                              : "var(--coral-accent)",
                            cursor: iStatus === "adding" || iStatus === "added" ? "default" : "pointer",
                            marginTop: 2,
                          }}
                        >
                          {iStatus === "adding"
                            ? copy.search.adding
                            : iStatus === "added"
                              ? copy.search.added
                              : intent === "reading"
                                ? copy.search.intentReadingAdd
                                : copy.search.intentWantToReadAdd}
                        </button>
                      );
                    })()
                  ) : (
                    <button
                      onClick={() => handleAdd(item)}
                      disabled={status === "adding"}
                      className="shrink-0 text-[13px] font-medium"
                      style={{
                        padding: "6px 14px",
                        borderRadius: "var(--coral-radius-sm)",
                        border:
                          status === "error"
                            ? "1px solid var(--coral-error)"
                            : "1px solid var(--coral-accent)",
                        backgroundColor: "transparent",
                        color:
                          status === "error"
                            ? "var(--coral-error)"
                            : "var(--coral-accent)",
                        cursor: status === "adding" ? "default" : "pointer",
                        transition:
                          "background-color var(--coral-transition), color var(--coral-transition)",
                        marginTop: 2,
                      }}
                    >
                      {status === "adding"
                        ? copy.search.adding
                        : status === "error"
                          ? copy.common.retry
                          : intent === "reading"
                            ? copy.search.intentReadingAdd
                            : intent === "want-to-read"
                              ? copy.search.intentWantToReadAdd
                              : copy.search.addToLibrary}
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <button
            onClick={() => setShowManual(true)}
            className="text-[13px] font-medium"
            style={{
              marginTop: 16,
              color: "var(--coral-accent)",
              background: "none",
              border: "none",
              cursor: "pointer",
            }}
          >
            {copy.search.manualEntry}
          </button>
        </>
      )}

      {/* 수동 등록 모달 */}
      {showManual && (
        <ManualEntryModal
          onClose={() => setShowManual(false)}
          onSuccess={() => {
            setShowManual(false);
            toast.show(copy.library.bookAdded);
          }}
        />
      )}
    </div>
  );
}

type CoverState = "empty" | "processing" | "preview" | "error";

function ManualEntryModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [publisher, setPublisher] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [isbn, setIsbn] = useState("");
  const [totalPages, setTotalPages] = useState("");
  const [translator, setTranslator] = useState("");
  const [artist, setArtist] = useState("");
  const [isEbook, setIsEbook] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  // 표지 업로드 상태
  const [coverState, setCoverState] = useState<CoverState>("empty");
  const [coverBlob, setCoverBlob] = useState<Blob | null>(null);
  const [coverPreviewUrl, setCoverPreviewUrl] = useState<string | null>(null);
  const [coverError, setCoverError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 모달 닫힐 때 objectURL 정리
  const handleClose = useCallback(() => {
    if (coverPreviewUrl) {
      URL.revokeObjectURL(coverPreviewUrl);
    }
    onClose();
  }, [coverPreviewUrl, onClose]);

  // 파일 선택 핸들러
  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      // input 값 리셋 (같은 파일 재선택 가능)
      e.target.value = "";
      if (!file) return;

      // type 체크
      if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
        setCoverError(copy.search.manualCoverErrorFormat);
        setCoverState("error");
        return;
      }

      // size 체크
      if (file.size > 10 * 1024 * 1024) {
        setCoverError(copy.search.manualCoverErrorSize);
        setCoverState("error");
        return;
      }

      setCoverState("processing");
      setCoverError(null);

      try {
        const bitmap = await createImageBitmap(file);

        const canvas = document.createElement("canvas");
        const maxDim = 500;
        const scale = Math.min(
          maxDim / bitmap.width,
          maxDim / bitmap.height,
          1
        );
        canvas.width = Math.round(bitmap.width * scale);
        canvas.height = Math.round(bitmap.height * scale);
        const ctx = canvas.getContext("2d")!;
        ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
        bitmap.close();

        const blob = await new Promise<Blob>((resolve) =>
          canvas.toBlob((b) => resolve(b!), "image/jpeg", 0.8)
        );

        // 이전 previewUrl 정리
        if (coverPreviewUrl) {
          URL.revokeObjectURL(coverPreviewUrl);
        }

        setCoverBlob(blob);
        setCoverPreviewUrl(URL.createObjectURL(blob));
        setCoverState("preview");
      } catch {
        setCoverError(copy.search.manualCoverErrorDecode);
        setCoverState("error");
      }
    },
    [coverPreviewUrl]
  );

  // 표지 제거
  const handleCoverRemove = useCallback(() => {
    if (coverPreviewUrl) {
      URL.revokeObjectURL(coverPreviewUrl);
    }
    setCoverBlob(null);
    setCoverPreviewUrl(null);
    setCoverError(null);
    setCoverState("empty");
  }, [coverPreviewUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    setError(null);

    let coverPath: string | null = null;

    // 표지 업로드
    if (coverBlob) {
      try {
        const supabase = createClient();
        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
          setError(copy.search.manualCoverErrorUpload);
          setLoading(false);
          return;
        }

        const path = `${user.id}/${crypto.randomUUID()}.jpg`;
        const { error: uploadError } = await supabase.storage
          .from("book-covers")
          .upload(path, coverBlob, { contentType: "image/jpeg" });

        if (uploadError) {
          setError(copy.search.manualCoverErrorUpload);
          setLoading(false);
          return;
        }

        coverPath = path;
      } catch {
        setError(copy.search.manualCoverErrorUpload);
        setLoading(false);
        return;
      }
    }

    const body: AddBookManualRequest = {
      type: "manual",
      title: title.trim(),
      author: author.trim() || null,
      publisher: publisher.trim() || null,
      cover_path: coverPath,
      isbn: isbn.trim() || null,
      total_pages: totalPages ? parseInt(totalPages, 10) : null,
      translator: translator.trim() || null,
      artist: artist.trim() || null,
      book_type: isEbook ? "eBook" : null,
    };

    const { error: apiError } = await api.post("/api/books", body);

    if (apiError) {
      // API 실패 시 업로드된 파일 best-effort 삭제
      if (coverPath) {
        try {
          const supabase = createClient();
          await supabase.storage.from("book-covers").remove([coverPath]);
        } catch {
          // best-effort
        }
      }
      setError(apiError);
      setLoading(false);
      return;
    }

    setLoading(false);
    onSuccess();
    router.push("/library");
    router.refresh();
  };

  // 표지 영역 렌더링
  const coverBoxStyle: React.CSSProperties = {
    width: 97,
    height: 140,
    borderRadius: 6,
    position: "relative",
    overflow: "hidden",
  };

  const renderCoverArea = () => {
    if (coverState === "empty" || coverState === "error") {
      return (
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center justify-center"
          style={{
            ...coverBoxStyle,
            border: "2px dashed var(--coral-border)",
            backgroundColor: "transparent",
            cursor: "pointer",
            gap: 6,
          }}
        >
          <ImagePlus
            size={24}
            style={{ color: "var(--coral-text-muted)" }}
          />
          <span
            className="text-[12px]"
            style={{ color: "var(--coral-text-muted)" }}
          >
            {copy.search.manualCoverSelect}
          </span>
        </button>
      );
    }

    if (coverState === "processing") {
      return (
        <div
          className="flex flex-col items-center justify-center"
          style={{
            ...coverBoxStyle,
            border: "2px dashed var(--coral-border)",
            backgroundColor: "var(--coral-bg)",
            gap: 8,
          }}
        >
          <Loader2
            size={20}
            className="animate-spin"
            style={{ color: "var(--coral-text-muted)" }}
          />
          <span
            className="text-[12px]"
            style={{ color: "var(--coral-text-muted)" }}
          >
            {copy.search.manualCoverProcessing}
          </span>
        </div>
      );
    }

    // preview
    return (
      <div className="flex flex-col items-center" style={{ gap: 8 }}>
        <div style={{ ...coverBoxStyle }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={coverPreviewUrl!}
            alt={copy.search.manualCoverSelect}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              borderRadius: 6,
              display: "block",
            }}
          />
          {loading && (
            <div
              className="absolute inset-0 flex items-center justify-center"
              style={{
                backgroundColor: "var(--coral-overlay)",
                borderRadius: 6,
              }}
            >
              <Loader2
                size={24}
                className="animate-spin"
                style={{ color: "var(--coral-surface)" }}
              />
            </div>
          )}
        </div>
        {!loading && (
          <div className="flex items-center" style={{ gap: 12 }}>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-[12px]"
              style={{
                color: "var(--coral-text-sub)",
                textDecoration: "underline",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: 0,
              }}
            >
              {copy.search.manualCoverReselect}
            </button>
            <button
              type="button"
              onClick={handleCoverRemove}
              className="text-[12px]"
              style={{
                color: "var(--coral-error)",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: 0,
              }}
            >
              {copy.search.manualCoverRemove}
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "var(--coral-overlay)" }}
      onClick={handleClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: "var(--coral-surface)",
          borderRadius: 12,
          padding: 24,
          width: "100%",
          maxWidth: 420,
          margin: "0 16px",
          maxHeight: "85dvh",
          overflowY: "auto",
        }}
      >
        <h3
          className="text-[16px] font-semibold"
          style={{ marginBottom: 20 }}
        >
          {copy.search.manualTitle}
        </h3>

        {/* 표지 선택 영역 */}
        <div
          className="flex flex-col items-center"
          style={{ marginBottom: 18 }}
        >
          {renderCoverArea()}
        </div>

        {/* 표지 에러 메시지 (인라인) */}
        {coverError && (
          <div
            className="text-[13px]"
            style={{
              marginBottom: 14,
              padding: "10px 14px",
              borderRadius: "var(--coral-radius)",
              backgroundColor: "var(--coral-error-bg)",
              color: "var(--coral-error)",
            }}
          >
            {coverError}
          </div>
        )}

        {/* 일반 에러 메시지 */}
        {error && (
          <div
            className="text-[13px]"
            style={{
              marginBottom: 14,
              padding: "10px 14px",
              borderRadius: "var(--coral-radius)",
              backgroundColor: "var(--coral-error-bg)",
              color: "var(--coral-error)",
            }}
          >
            {error}
          </div>
        )}

        {/* hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileChange}
          hidden
        />

        <form
          onSubmit={handleSubmit}
          className="flex flex-col"
          style={{ gap: 14 }}
        >
          <div>
            <label
              className="block text-[13px] font-medium"
              style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
            >
              {copy.library.titleLabel}
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={copy.search.manualTitlePlaceholder}
              className="w-full text-[14px] outline-none"
              style={{
                padding: "10px 12px",
                border: "1px solid var(--coral-border)",
                borderRadius: "var(--coral-radius)",
              }}
            />
          </div>
          <div>
            <label
              className="block text-[13px] font-medium"
              style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
            >
              {copy.bookDetail.authorLabel}
            </label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder={copy.search.manualAuthorPlaceholder}
              className="w-full text-[14px] outline-none"
              style={{
                padding: "10px 12px",
                border: "1px solid var(--coral-border)",
                borderRadius: "var(--coral-radius)",
              }}
            />
          </div>
          <div>
            <label
              className="block text-[13px] font-medium"
              style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
            >
              {copy.bookDetail.publisherLabel}
            </label>
            <input
              type="text"
              value={publisher}
              onChange={(e) => setPublisher(e.target.value)}
              placeholder={copy.search.manualPublisherPlaceholder}
              className="w-full text-[14px] outline-none"
              style={{
                padding: "10px 12px",
                border: "1px solid var(--coral-border)",
                borderRadius: "var(--coral-radius)",
              }}
            />
          </div>

          {/* v1.4.7 추가 정보 아코디언 */}
          <button
            type="button"
            onClick={() => setMoreOpen(!moreOpen)}
            className="flex items-center text-[13px]"
            style={{
              color: "var(--coral-text-sub)",
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: 0,
              gap: 4,
            }}
          >
            <span>{copy.search.manualMoreInfo}</span>
            {moreOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {moreOpen && (
            <div className="flex flex-col" style={{ gap: 14 }}>
              <div>
                <label
                  className="block text-[13px] font-medium"
                  style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
                >
                  {copy.bookDetail.isbnLabel}
                </label>
                <input
                  type="text"
                  value={isbn}
                  onChange={(e) => setIsbn(e.target.value)}
                  placeholder={copy.search.manualIsbnPlaceholder}
                  className="w-full text-[14px] outline-none"
                  style={{
                    padding: "10px 12px",
                    border: "1px solid var(--coral-border)",
                    borderRadius: "var(--coral-radius)",
                  }}
                />
              </div>
              <div>
                <label
                  className="block text-[13px] font-medium"
                  style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
                >
                  {copy.bookDetail.pagesLabel}
                </label>
                <input
                  type="number"
                  value={totalPages}
                  onChange={(e) => setTotalPages(e.target.value)}
                  placeholder={copy.search.manualPagesPlaceholder}
                  className="w-full text-[14px] outline-none"
                  style={{
                    padding: "10px 12px",
                    border: "1px solid var(--coral-border)",
                    borderRadius: "var(--coral-radius)",
                  }}
                />
              </div>
              <div>
                <label
                  className="block text-[13px] font-medium"
                  style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
                >
                  {copy.bookDetail.translatorLabel}
                </label>
                <input
                  type="text"
                  value={translator}
                  onChange={(e) => setTranslator(e.target.value)}
                  placeholder={copy.search.manualTranslatorPlaceholder}
                  className="w-full text-[14px] outline-none"
                  style={{
                    padding: "10px 12px",
                    border: "1px solid var(--coral-border)",
                    borderRadius: "var(--coral-radius)",
                  }}
                />
              </div>
              <div>
                <label
                  className="block text-[13px] font-medium"
                  style={{ marginBottom: 6, color: "var(--coral-text-sub)" }}
                >
                  {copy.bookDetail.artistLabel}
                </label>
                <input
                  type="text"
                  value={artist}
                  onChange={(e) => setArtist(e.target.value)}
                  placeholder={copy.search.manualArtistPlaceholder}
                  className="w-full text-[14px] outline-none"
                  style={{
                    padding: "10px 12px",
                    border: "1px solid var(--coral-border)",
                    borderRadius: "var(--coral-radius)",
                  }}
                />
              </div>
              <label
                className="flex items-center text-[13px] cursor-pointer"
                style={{ gap: 8, color: "var(--coral-text-sub)" }}
              >
                <input
                  type="checkbox"
                  checked={isEbook}
                  onChange={(e) => setIsEbook(e.target.checked)}
                  style={{ accentColor: "var(--coral-accent)" }}
                />
                {copy.bookDetail.ebookLabel}
              </label>
            </div>
          )}

          <div
            className="flex justify-end"
            style={{ gap: 8, marginTop: 4 }}
          >
            <button
              type="button"
              onClick={handleClose}
              className="text-[13px] font-medium"
              style={{
                padding: "8px 16px",
                borderRadius: "var(--coral-radius-sm)",
                border: "1px solid var(--coral-border)",
                color: "var(--coral-text-sub)",
              }}
            >
              {copy.common.cancel}
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim()}
              className="text-[13px] font-medium disabled:opacity-60"
              style={{
                padding: "8px 16px",
                borderRadius: "var(--coral-radius-sm)",
                backgroundColor: "var(--coral-accent)",
                color: "var(--primary-foreground)",
                border: "none",
              }}
            >
              {loading ? copy.common.loading : copy.search.manualSubmit}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
