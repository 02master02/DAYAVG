(function () {
    const STORAGE_KEY = "dayavg.assetSnapshot.v1";

    function isValidSnapshot(payload) {
        if (!payload || typeof payload !== "object") {
            return false;
        }

        if (payload.schema_version !== 1 || !Array.isArray(payload.items)) {
            return false;
        }

        return payload.items.every((item) => {
            if (!item || typeof item !== "object") {
                return false;
            }

            const hasValidRequiredFields =
                Number.isInteger(item.id) &&
                item.id > 0 &&
                typeof item.item_name === "string" &&
                item.item_name.trim() !== "" &&
                Number.isInteger(item.price_cents) &&
                item.price_cents > 0 &&
                typeof item.purchase_date === "string" &&
                typeof item.created_at === "string";

            const hasValidOptionalFields =
                (item.retired_on === null || typeof item.retired_on === "string") &&
                (item.retired_note === null || typeof item.retired_note === "string");

            return hasValidRequiredFields && hasValidOptionalFields;
        });
    }

    function syncSnapshotToLocalStorage() {
        const snapshotNode = document.getElementById("asset-snapshot");
        if (!snapshotNode) {
            return;
        }

        try {
            const payload = JSON.parse(snapshotNode.textContent || "{}");
            if (!isValidSnapshot(payload)) {
                return;
            }

            localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            console.warn("DayAvg localStorage sync skipped:", error);
        }
    }

    function setImportFeedback(message) {
        const feedback = document.querySelector("[data-import-feedback]");
        if (!(feedback instanceof HTMLElement)) {
            return;
        }
        feedback.textContent = message;
    }

    async function validateImportFile(file) {
        try {
            const rawText = await file.text();
            const payload = JSON.parse(rawText);
            return isValidSnapshot(payload);
        } catch (_error) {
            return false;
        }
    }

    function bindImportValidation() {
        const form = document.querySelector("[data-import-form]");
        const fileInput = document.querySelector("[data-import-file]");
        if (!(form instanceof HTMLFormElement) || !(fileInput instanceof HTMLInputElement)) {
            return;
        }

        form.addEventListener("submit", async (event) => {
            const file = fileInput.files && fileInput.files[0];
            if (!file) {
                setImportFeedback("请选择要导入的 JSON 文件。");
                event.preventDefault();
                return;
            }

            const isValid = await validateImportFile(file);
            if (!isValid) {
                setImportFeedback("导入文件格式不正确，当前数据未被修改。");
                fileInput.value = "";
                event.preventDefault();
                return;
            }

            setImportFeedback("");
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        syncSnapshotToLocalStorage();
        bindImportValidation();
    });
})();
