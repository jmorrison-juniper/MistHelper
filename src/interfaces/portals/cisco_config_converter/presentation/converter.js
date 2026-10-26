/* Keep source-derived data in page memory only. */
class CiscoProposalPage {
    constructor() {
        this.form = document.getElementById("cisco-upload");
        this.review = document.getElementById("cisco-review");
        this.export = document.getElementById("cisco-export");
        this.proposal = null;
        this.bind();
    }

    bind() {
        this.form.addEventListener("input", () => this.reset());
        this.form.addEventListener("submit", (event) => this.preview(event));
        this.review.addEventListener("click", () => this.action("review"));
        this.export.addEventListener("click", () => this.action("export"));
        window.addEventListener("pagehide", () => this.reset());
    }

    reset() {
        this.proposal = null;
        this.review.disabled = true;
        this.export.disabled = true;
        document.getElementById("cisco-proposal").textContent = "";
    }

    async preview(event) {
        event.preventDefault();
        this.reset();
        const generation = {};
        this.proposal = generation;
        try {
            const response = await fetch("/cisco-config-converter/preview", {
                method: "POST", body: new FormData(this.form), cache: "no-store"
            });
            const value = await CiscoProposalTransport.result(response);
            if (this.proposal !== generation) return;
            this.proposal = value;
            document.getElementById("cisco-proposal").textContent = JSON.stringify(value, null, 2);
            this.review.disabled = false;
            document.getElementById("cisco-status").textContent = "Review unsupported items and known gaps before export.";
        } catch (error) {
            if (this.proposal !== generation) return;
            this.reset();
            document.getElementById("cisco-status").textContent = error.message;
        }
    }

    async action(operation) {
        const proposal = this.proposal;
        this.review.disabled = true;
        this.export.disabled = true;
        try {
            const response = await fetch(`/cisco-config-converter/${operation}`, {
                method: "POST", cache: "no-store",
                headers: {"Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content},
                body: JSON.stringify(proposal)
            });
            const value = await CiscoProposalTransport.result(response);
            if (this.proposal !== proposal) return;
            if (operation === "export") CiscoProposalTransport.download(value);
            this.export.disabled = false;
            document.getElementById("cisco-status").textContent = operation === "review" ? "Proposal reviewed." : "JSON exported. Mist was not changed.";
        } catch (error) {
            document.getElementById("cisco-status").textContent = error.message;
            this.review.disabled = this.proposal === null;
        }
    }

}

/* Handle HTTP failures and the explicit operator download. */
class CiscoProposalTransport {
    static async result(response) {
        if (!(response.headers.get("Content-Type") || "").includes("application/json")) {
            throw new Error("The request failed. Create a new preview or reload the page.");
        }
        const value = await response.json();
        if (!response.ok) throw new Error(value.error || "The request failed.");
        return value;
    }

    static download(value) {
        const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type: "application/json"}));
        const link = document.createElement("a");
        link.href = url;
        link.download = "cisco-proposal.json";
        link.click();
        URL.revokeObjectURL(url);
    }
}

new CiscoProposalPage();
