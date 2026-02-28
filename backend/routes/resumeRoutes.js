import express from "express";
import { uploadResume } from "../controllers/resumeController.js";
import upload from "../middleware/uploadMiddleware.js";
import { protect } from "../middleware/authMiddleware.js";

const router = express.Router();

router.post("/upload", protect, upload.single("resume"), uploadResume);

export default router;