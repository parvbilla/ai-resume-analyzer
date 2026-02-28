import Resume from "../models/Resume.js";
import cloudinary from "../config/cloudinary.js";
import pdfParse from "pdf-parse";
import fs from "fs";

export const uploadResume = async (req, res) => {
  try {
    const filePath = req.file.path;

    // Upload to Cloudinary
    const result = await cloudinary.uploader.upload(filePath, {
      resource_type: "raw",
      folder: "resumes",
    });

    // Parse PDF
    const pdfBuffer = fs.readFileSync(filePath);
    const data = await pdfParse(pdfBuffer);

    // Save to DB
    const resume = await Resume.create({
      user: req.user._id,
      fileUrl: result.secure_url,
      extractedText: data.text,
    });

    // Delete local file
    fs.unlinkSync(filePath);

    res.status(201).json({
      message: "Resume uploaded successfully",
      resume,
    });

  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};