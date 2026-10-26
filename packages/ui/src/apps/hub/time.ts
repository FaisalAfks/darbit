// Times for people: 125 seconds -> "2 m", 187 000 -> "2 d 4 h".

export function inTime(seconds: number): string {
  if (seconds < 60) return "now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ${minutes % 60} m`;
  return `${Math.floor(hours / 24)} d ${hours % 24} h`;
}

/** A report time ("2026-10-26T10:04:31.120" or "10:04:31") as "10:04". */
export function clock(time: string | null | undefined): string {
  if (!time) return "";
  const at = time.includes("T") ? time.split("T")[1] : time;
  return at.slice(0, 5);
}

/** A length of time for people: 38 160 seconds -> "10 h 36 m", 300 -> "5 m", 40 -> "40 s". */
export function duration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)} s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} m`;
  return `${Math.floor(minutes / 60)} h ${minutes % 60} m`;
}
